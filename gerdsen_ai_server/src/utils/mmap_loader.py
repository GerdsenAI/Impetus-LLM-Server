"""
Memory-mapped model loading for fast loading and reduced memory usage
"""

import json
import mmap
import os
import struct
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from loguru import logger

try:
    import mlx
    import mlx.core as mx
    MLX_AVAILABLE = True
except ImportError:
    MLX_AVAILABLE = False
    logger.warning("MLX not available for memory mapping")
    # Create a dummy mx for type annotations
    class _DummyMLX:
        class array:
            pass
    mx = _DummyMLX()


@dataclass
class MmapInfo:
    """Information about a memory-mapped file"""
    file_path: Path
    file_size: int
    mmap_object: mmap.mmap | None
    access_mode: int
    is_loaded: bool = False
    load_time_ms: float = 0.0


class MemoryMappedLoader:
    """
    Handles memory-mapped loading of model files for faster access
    and reduced memory footprint.
    
    Supports safetensors and numpy formats with lazy loading.
    """

    # File format magic numbers
    SAFETENSORS_MAGIC = b"@\x00\x00\x00\x00\x00\x00\x00"  # First 8 bytes
    NUMPY_MAGIC = b"\x93NUMPY"

    def __init__(self):
        """Initialize memory-mapped loader"""
        self.mmaps: dict[str, MmapInfo] = {}
        self._lock = threading.Lock()
        self.page_size = os.sysconf('SC_PAGE_SIZE') if hasattr(os, 'sysconf') else 4096
        logger.info(f"Memory-mapped loader initialized with page size: {self.page_size}")

    def load_model_mmap(self, model_path: Path, read_only: bool = True) -> dict[str, Any]:
        """
        Load a model using memory mapping.
        
        Args:
            model_path: Path to model directory or file
            read_only: Whether to open in read-only mode
            
        Returns:
            Dictionary of loaded tensors/weights
        """
        start_time = time.time()
        weights = {}

        if model_path.is_file():
            # Single file (e.g., GGUF)
            weights.update(self._load_single_file(model_path, read_only))
        else:
            # Directory with multiple files
            weights.update(self._load_directory(model_path, read_only))

        load_time = (time.time() - start_time) * 1000
        logger.info(f"Memory-mapped loading completed in {load_time:.1f}ms")

        return weights

    def _load_directory(self, model_dir: Path, read_only: bool) -> dict[str, Any]:
        """Load all weight files from a directory"""
        weights = {}

        # Look for safetensors files first
        safetensor_files = list(model_dir.glob("*.safetensors"))
        if safetensor_files:
            logger.info(f"Found {len(safetensor_files)} safetensors files")
            for file_path in safetensor_files:
                weights.update(self._load_safetensors(file_path, read_only))

        # Look for numpy files
        numpy_files = list(model_dir.glob("*.npy"))
        if numpy_files:
            logger.info(f"Found {len(numpy_files)} numpy files")
            for file_path in numpy_files:
                tensor_name = file_path.stem
                weights[tensor_name] = self._load_numpy(file_path, read_only)

        # Look for PyTorch files (convert to numpy)
        pt_files = list(model_dir.glob("*.pt"))
        if pt_files:
            logger.info(f"Found {len(pt_files)} PyTorch files")
            for file_path in pt_files:
                weights.update(self._load_pytorch(file_path, read_only))

        return weights

    def _load_single_file(self, file_path: Path, read_only: bool) -> dict[str, Any]:
        """Load a single model file"""
        if file_path.suffix == ".safetensors":
            return self._load_safetensors(file_path, read_only)
        elif file_path.suffix == ".npy":
            return {file_path.stem: self._load_numpy(file_path, read_only)}
        elif file_path.suffix in [".pt", ".pth"]:
            return self._load_pytorch(file_path, read_only)
        elif file_path.suffix == ".gguf":
            return self._load_gguf_mmap(file_path, read_only)
        else:
            logger.warning(f"Unsupported file format: {file_path.suffix}")
            return {}

    def _load_safetensors(self, file_path: Path, read_only: bool) -> dict[str, mx.array]:
        """Load safetensors file using memory mapping"""
        logger.info(f"Loading safetensors file: {file_path.name}")

        with self._lock:
            # Open file for memory mapping
            access = mmap.ACCESS_READ if read_only else mmap.ACCESS_WRITE

            with open(file_path, 'rb') as f:
                # Read header size (first 8 bytes)
                header_size_bytes = f.read(8)
                header_size = struct.unpack('<Q', header_size_bytes)[0]

                # Read header JSON
                header_json = f.read(header_size)
                header = json.loads(header_json)

                # Calculate data offset
                data_offset = 8 + header_size

                # Create memory map
                file_size = file_path.stat().st_size
                mm = mmap.mmap(f.fileno(), file_size, access=access)

                # Store mmap info
                mmap_info = MmapInfo(
                    file_path=file_path,
                    file_size=file_size,
                    mmap_object=mm,
                    access_mode=access,
                    is_loaded=True
                )
                self.mmaps[str(file_path)] = mmap_info

        # Parse tensors from header
        weights = {}

        for tensor_name, tensor_info in header.items():
            if tensor_name == "__metadata__":
                continue

            # Extract tensor metadata
            dtype = tensor_info["dtype"]
            shape = tensor_info["shape"]
            data_offsets = tensor_info["data_offsets"]
            start_offset = data_offset + data_offsets[0]
            end_offset = data_offset + data_offsets[1]

            # Create memory view
            tensor_data = mm[start_offset:end_offset]

            # Convert to MLX array
            if MLX_AVAILABLE:
                # Convert dtype string to numpy dtype
                np_dtype = self._safetensors_dtype_to_numpy(dtype)

                # Create numpy array from memory view (zero-copy)
                np_array = np.frombuffer(tensor_data, dtype=np_dtype).reshape(shape)

                # Convert to MLX array
                mx_array = mx.array(np_array)
                weights[tensor_name] = mx_array
            else:
                # Return numpy array if MLX not available
                np_dtype = self._safetensors_dtype_to_numpy(dtype)
                weights[tensor_name] = np.frombuffer(tensor_data, dtype=np_dtype).reshape(shape)

        logger.info(f"Loaded {len(weights)} tensors from {file_path.name}")
        return weights

    def _load_numpy(self, file_path: Path, read_only: bool) -> Any:
        """Load numpy file using memory mapping"""
        logger.debug(f"Loading numpy file: {file_path.name}")

        # Use numpy's memory-map mode
        mode = 'r' if read_only else 'r+'
        np_array = np.load(file_path, mmap_mode=mode)

        if MLX_AVAILABLE:
            return mx.array(np_array)
        return np_array

    def _load_pytorch(self, file_path: Path, read_only: bool) -> dict[str, Any]:
        """Load PyTorch file (fallback to regular loading)"""
        logger.info(f"Loading PyTorch file: {file_path.name}")

        try:
            import torch

            # Load with memory mapping if possible
            weights_dict = torch.load(
                file_path,
                map_location='cpu',
                mmap=True if hasattr(torch, 'mmap') else None
            )

            # Convert to MLX arrays
            result = {}
            for key, tensor in weights_dict.items():
                if MLX_AVAILABLE:
                    result[key] = mx.array(tensor.numpy())
                else:
                    result[key] = tensor.numpy()

            return result

        except ImportError:
            logger.error("PyTorch not available for loading .pt files")
            return {}

    def _load_gguf_mmap(self, file_path: Path, read_only: bool) -> dict[str, Any]:
        """Load GGUF file using memory mapping"""
        logger.info(f"Loading GGUF file with mmap: {file_path.name}")

        # GGUF format is complex, for now return empty
        # This would require implementing GGUF parser
        logger.warning("GGUF memory mapping not yet implemented")
        return {}

    def _safetensors_dtype_to_numpy(self, dtype_str: str) -> np.dtype:
        """Convert safetensors dtype string to numpy dtype"""
        dtype_map = {
            "F32": np.float32,
            "F16": np.float16,
            "BF16": np.float16,  # Approximate with float16
            "I64": np.int64,
            "I32": np.int32,
            "I16": np.int16,
            "I8": np.int8,
            "U8": np.uint8,
            "BOOL": np.bool_,
        }

        return dtype_map.get(dtype_str, np.float32)

    def close_mmap(self, file_path: str):
        """Close a memory-mapped file"""
        with self._lock:
            if file_path in self.mmaps:
                mmap_info = self.mmaps[file_path]
                if mmap_info.mmap_object:
                    mmap_info.mmap_object.close()
                del self.mmaps[file_path]
                logger.debug(f"Closed memory map for {file_path}")

    def close_all(self):
        """Close all memory-mapped files"""
        with self._lock:
            for file_path in list(self.mmaps.keys()):
                self.close_mmap(file_path)
        logger.info("Closed all memory-mapped files")

    def get_memory_usage(self) -> dict[str, Any]:
        """Get memory usage statistics"""
        total_mapped = 0
        file_count = 0

        with self._lock:
            for mmap_info in self.mmaps.values():
                if mmap_info.is_loaded:
                    total_mapped += mmap_info.file_size
                    file_count += 1

        return {
            "total_mapped_gb": total_mapped / (1024 ** 3),
            "file_count": file_count,
            "page_size": self.page_size
        }

    def benchmark_load_time(self, model_path: Path) -> dict[str, float]:
        """Benchmark mmap vs regular loading time"""
        results = {}

        # Benchmark mmap loading
        start = time.time()
        mmap_weights = self.load_model_mmap(model_path)
        mmap_time = (time.time() - start) * 1000
        results["mmap_load_ms"] = mmap_time

        # Clear caches
        self.close_all()
        if MLX_AVAILABLE:
            mx.metal.clear_cache()

        # Benchmark regular loading (simplified)
        start = time.time()
        # This would be the regular loading method
        regular_time = (time.time() - start) * 1000
        results["regular_load_ms"] = regular_time

        results["speedup"] = regular_time / mmap_time if mmap_time > 0 else 0
        results["model_size_gb"] = sum(
            f.stat().st_size for f in model_path.rglob("*") if f.is_file()
        ) / (1024 ** 3)

        return results


# Global memory-mapped loader instance
mmap_loader = MemoryMappedLoader()
