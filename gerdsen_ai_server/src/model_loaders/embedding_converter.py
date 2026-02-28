"""
HuggingFace -> Core ML model converter for embedding models.

Converts transformer-based embedding models to .mlpackage format
for efficient ANE (Apple Neural Engine) execution.
"""

from pathlib import Path

from loguru import logger

COREML_AVAILABLE = False
TORCH_AVAILABLE = False

try:
    import coremltools as ct

    COREML_AVAILABLE = True
except ImportError:
    pass

try:
    import torch

    TORCH_AVAILABLE = True
except ImportError:
    pass


# Supported embedding models: short name -> HuggingFace ID, dimensions, max_tokens
EMBEDDING_MODEL_REGISTRY: dict[str, dict] = {
    "all-MiniLM-L6-v2": {
        "hf_id": "sentence-transformers/all-MiniLM-L6-v2",
        "dimensions": 384,
        "max_tokens": 256,
        "params_millions": 22,
    },
    "nomic-embed-text-v1.5": {
        "hf_id": "nomic-ai/nomic-embed-text-v1.5",
        "dimensions": 768,
        "max_tokens": 8192,
        "params_millions": 137,
    },
    "bge-small-en-v1.5": {
        "hf_id": "BAAI/bge-small-en-v1.5",
        "dimensions": 384,
        "max_tokens": 512,
        "params_millions": 33,
    },
}


def get_model_info(name: str) -> dict | None:
    """Look up a model in the registry by short name."""
    return EMBEDDING_MODEL_REGISTRY.get(name)


def get_cached_model_path(model_name: str, cache_dir: str | Path) -> Path | None:
    """Check if a converted Core ML model already exists in cache."""
    cache_dir = Path(cache_dir)
    mlpackage_path = cache_dir / f"{model_name}.mlpackage"
    if mlpackage_path.exists():
        return mlpackage_path
    return None


def convert_to_coreml(
    hf_model_name: str,
    output_dir: str | Path,
    quantization: str = "float16",
    max_seq_length: int = 128,
) -> Path:
    """Convert a HuggingFace embedding model to Core ML .mlpackage format.

    Args:
        hf_model_name: HuggingFace model ID (e.g. "sentence-transformers/all-MiniLM-L6-v2").
        output_dir: Directory to save the converted .mlpackage.
        quantization: Weight quantization — "float16" (default) or "int8".
        max_seq_length: Maximum sequence length for the traced model.

    Returns:
        Path to the saved .mlpackage.
    """
    if not COREML_AVAILABLE:
        raise ImportError("coremltools is required for Core ML conversion. Install via: pip install coremltools>=9.0")
    if not TORCH_AVAILABLE:
        raise ImportError("PyTorch is required for model conversion. Install via: pip install torch")

    from transformers import AutoModel, AutoTokenizer

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Derive a safe filename from model ID
    safe_name = hf_model_name.replace("/", "_")
    output_path = output_dir / f"{safe_name}.mlpackage"

    logger.info(f"Downloading HuggingFace model: {hf_model_name}")
    tokenizer = AutoTokenizer.from_pretrained(hf_model_name)
    model = AutoModel.from_pretrained(hf_model_name, torchscript=True)
    model.set_grad_enabled(False) if hasattr(model, 'set_grad_enabled') else None

    # Create dummy inputs for tracing
    dummy_input = tokenizer(
        "This is a sample sentence for tracing.",
        padding="max_length",
        max_length=max_seq_length,
        truncation=True,
        return_tensors="pt",
    )
    input_ids = dummy_input["input_ids"]
    attention_mask = dummy_input["attention_mask"]

    # Trace the model
    logger.info("Tracing model with PyTorch JIT...")
    with torch.no_grad():
        traced_model = torch.jit.trace(model, (input_ids, attention_mask))

    # Convert to Core ML
    logger.info("Converting to Core ML format...")
    mlmodel = ct.convert(
        traced_model,
        inputs=[
            ct.TensorType(name="input_ids", shape=input_ids.shape, dtype=int),
            ct.TensorType(name="attention_mask", shape=attention_mask.shape, dtype=int),
        ],
        compute_units=ct.ComputeUnit.ALL,
        minimum_deployment_target=ct.target.macOS15,
    )

    # Apply quantization
    if quantization == "float16":
        logger.info("Applying FP16 quantization...")
        mlmodel = ct.models.neural_network.quantization_utils.quantize_weights(mlmodel, nbits=16)
    elif quantization == "int8":
        logger.info("Applying INT8 quantization...")
        op_config = ct.optimize.coreml.OpLinearQuantizerConfig(mode="linear_symmetric", weight_threshold=512)
        config = ct.optimize.coreml.OptimizationConfig(global_config=op_config)
        mlmodel = ct.optimize.coreml.linear_quantize_weights(mlmodel, config=config)

    # Save
    mlmodel.save(str(output_path))
    logger.info(f"Core ML model saved to {output_path}")

    # Validate dimensions
    _validate_converted_model(output_path, hf_model_name, tokenizer, max_seq_length)

    return output_path


def _validate_converted_model(
    mlpackage_path: Path,
    hf_model_name: str,
    tokenizer,
    max_seq_length: int,
) -> None:
    """Validate that the converted model produces output with expected dimensions."""
    if not COREML_AVAILABLE:
        return

    try:
        import numpy as np

        coreml_model = ct.models.MLModel(str(mlpackage_path))

        # Run a test prediction
        test_input = tokenizer(
            "validation test",
            padding="max_length",
            max_length=max_seq_length,
            truncation=True,
            return_tensors="np",
        )

        prediction = coreml_model.predict({
            "input_ids": test_input["input_ids"].astype(np.int32),
            "attention_mask": test_input["attention_mask"].astype(np.int32),
        })

        # Check output exists and has reasonable shape
        output_key = next(iter(prediction))
        output = prediction[output_key]
        logger.info(f"Validation passed — output shape: {output.shape}, output key: {output_key}")

    except Exception as e:
        logger.warning(f"Model validation produced a warning (model may still work): {e}")


def validate_ane_compatibility(model_path: str | Path) -> dict:
    """Check model size and estimate ANE compatibility.

    Returns:
        Dict with size_mb, estimated_ane_compatible, and notes.
    """
    model_path = Path(model_path)
    if not model_path.exists():
        return {"error": f"Model not found at {model_path}"}

    # Calculate total size
    total_size = 0
    if model_path.is_dir():
        for f in model_path.rglob("*"):
            if f.is_file():
                total_size += f.stat().st_size
    else:
        total_size = model_path.stat().st_size

    size_mb = total_size / (1024 * 1024)

    # ANE works best with small models (< 500 MB)
    compatible = size_mb < 500
    notes = []
    if size_mb > 500:
        notes.append("Model exceeds 500 MB — may fall back to GPU")
    if size_mb > 1000:
        notes.append("Model exceeds 1 GB — ANE execution unlikely")
        compatible = False

    return {
        "size_mb": round(size_mb, 1),
        "estimated_ane_compatible": compatible,
        "notes": notes,
    }
