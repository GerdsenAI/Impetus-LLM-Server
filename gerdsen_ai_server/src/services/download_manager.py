"""
Download Manager Service - Handles model downloads from HuggingFace Hub
"""

import os
import asyncio
import shutil
from pathlib import Path
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
from loguru import logger

try:
    from huggingface_hub import snapshot_download, hf_hub_download
    from huggingface_hub.utils import HfHubHTTPError
    HF_HUB_AVAILABLE = True
except ImportError:
    logger.warning("huggingface_hub not available, model downloading will be limited")
    HF_HUB_AVAILABLE = False

from ..config.settings import settings


class DownloadStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class DownloadTask:
    """Download task information"""
    task_id: str
    model_id: str
    status: DownloadStatus
    progress: float = 0.0
    downloaded_bytes: int = 0
    total_bytes: int = 0
    speed_mbps: float = 0.0
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    eta_seconds: Optional[int] = None
    local_path: Optional[Path] = None


@dataclass
class DownloadProgress:
    """Progress information for callbacks"""
    task_id: str
    downloaded_bytes: int
    total_bytes: int
    speed_mbps: float
    eta_seconds: int


class DownloadManager:
    """Manages model downloads with progress tracking"""
    
    def __init__(self, models_dir: Optional[Path] = None):
        self.models_dir = models_dir or settings.model.models_dir
        self.downloads_dir = self.models_dir / "downloads"
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        
        self.tasks: Dict[str, DownloadTask] = {}
        self.progress_callbacks: Dict[str, Callable[[DownloadProgress], None]] = {}
        self._download_semaphore = asyncio.Semaphore(2)  # Max 2 concurrent downloads
        
        # Enable HF_TRANSFER for faster downloads if available
        try:
            import hf_transfer
            os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
            logger.info("HF Transfer enabled for faster downloads")
        except ImportError:
            logger.info("Install hf_transfer for 5x faster downloads: pip install hf_transfer")
    
    def create_download_task(self, model_id: str) -> str:
        """Create a new download task"""
        task_id = str(uuid.uuid4())
        task = DownloadTask(
            task_id=task_id,
            model_id=model_id,
            status=DownloadStatus.PENDING
        )
        self.tasks[task_id] = task
        logger.info(f"Created download task {task_id} for model {model_id}")
        return task_id
    
    def register_progress_callback(self, task_id: str, 
                                 callback: Callable[[DownloadProgress], None]):
        """Register a callback for progress updates"""
        self.progress_callbacks[task_id] = callback
    
    def get_task_status(self, task_id: str) -> Optional[DownloadTask]:
        """Get current status of a download task"""
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> Dict[str, DownloadTask]:
        """Get all download tasks"""
        return self.tasks.copy()
    
    def cancel_download(self, task_id: str) -> bool:
        """Cancel a download task"""
        task = self.tasks.get(task_id)
        if not task or task.status not in [DownloadStatus.PENDING, DownloadStatus.DOWNLOADING]:
            return False
        
        task.status = DownloadStatus.CANCELLED
        logger.info(f"Cancelled download task {task_id}")
        return True
    
    def check_disk_space(self, required_gb: float) -> tuple[bool, float]:
        """Check if enough disk space is available"""
        stat = shutil.disk_usage(self.models_dir)
        available_gb = stat.free / (1024 ** 3)
        has_space = available_gb >= required_gb * 1.2  # 20% buffer
        return has_space, available_gb
    
    async def download_model(self, task_id: str, 
                           progress_callback: Optional[Callable] = None) -> bool:
        """Download a model with progress tracking"""
        task = self.tasks.get(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return False
        
        if not HF_HUB_AVAILABLE:
            task.status = DownloadStatus.FAILED
            task.error = "huggingface_hub is not installed"
            return False
        
        async with self._download_semaphore:
            try:
                task.status = DownloadStatus.DOWNLOADING
                task.started_at = datetime.now()
                
                # Determine local path
                model_name = task.model_id.replace("/", "_")
                local_path = self.models_dir / model_name
                temp_path = self.downloads_dir / model_name
                
                # Create progress tracker
                def hf_progress_callback(progress_dict: Dict[str, Any]):
                    """HuggingFace Hub progress callback"""
                    if task.status == DownloadStatus.CANCELLED:
                        raise InterruptedError("Download cancelled")
                    
                    # Update task progress
                    if 'downloaded' in progress_dict and 'total' in progress_dict:
                        task.downloaded_bytes = progress_dict['downloaded']
                        task.total_bytes = progress_dict['total']
                        task.progress = task.downloaded_bytes / task.total_bytes if task.total_bytes > 0 else 0
                        
                        # Calculate speed and ETA
                        if task.started_at:
                            elapsed = (datetime.now() - task.started_at).total_seconds()
                            if elapsed > 0:
                                task.speed_mbps = (task.downloaded_bytes / (1024 * 1024)) / elapsed
                                if task.speed_mbps > 0:
                                    remaining_bytes = task.total_bytes - task.downloaded_bytes
                                    task.eta_seconds = int(remaining_bytes / (task.speed_mbps * 1024 * 1024))
                    
                    # Call registered callback
                    if task_id in self.progress_callbacks:
                        progress = DownloadProgress(
                            task_id=task_id,
                            downloaded_bytes=task.downloaded_bytes,
                            total_bytes=task.total_bytes,
                            speed_mbps=task.speed_mbps,
                            eta_seconds=task.eta_seconds or 0
                        )
                        self.progress_callbacks[task_id](progress)
                    
                    # Call provided callback
                    if progress_callback:
                        progress_callback(task)
                
                # Download in separate thread to not block event loop
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    lambda: snapshot_download(
                        repo_id=task.model_id,
                        local_dir=str(temp_path),
                        local_dir_use_symlinks=False,
                        resume_download=True,
                        # progress_callback=hf_progress_callback  # Note: Not directly supported
                    )
                )
                
                # Move from temp to final location
                if temp_path.exists():
                    if local_path.exists():
                        shutil.rmtree(local_path)
                    shutil.move(str(temp_path), str(local_path))
                    task.local_path = local_path
                
                task.status = DownloadStatus.COMPLETED
                task.completed_at = datetime.now()
                task.progress = 1.0
                
                logger.info(f"Successfully downloaded model {task.model_id} to {local_path}")
                return True
                
            except InterruptedError:
                task.status = DownloadStatus.CANCELLED
                logger.info(f"Download cancelled for {task.model_id}")
                return False
                
            except HfHubHTTPError as e:
                task.status = DownloadStatus.FAILED
                task.error = f"HuggingFace Hub error: {str(e)}"
                logger.error(f"HF Hub error downloading {task.model_id}: {e}")
                return False
                
            except Exception as e:
                task.status = DownloadStatus.FAILED
                task.error = str(e)
                logger.error(f"Error downloading model {task.model_id}: {e}")
                return False
    
    def cleanup_failed_downloads(self):
        """Clean up incomplete downloads"""
        for item in self.downloads_dir.iterdir():
            if item.is_dir():
                # Check if it's an incomplete download
                if not (item / "config.json").exists():
                    logger.info(f"Cleaning up incomplete download: {item}")
                    shutil.rmtree(item)
    
    def get_download_size(self, model_id: str) -> Optional[float]:
        """Estimate download size for a model (in GB)"""
        # This is a rough estimate based on model naming conventions
        # In production, you'd query the HF API for exact sizes
        if "3b" in model_id.lower() or "3B" in model_id:
            return 2.0 if "4bit" in model_id else 4.0
        elif "7b" in model_id.lower() or "7B" in model_id:
            return 4.0 if "4bit" in model_id else 8.0
        elif "8b" in model_id.lower() or "8B" in model_id:
            return 4.5 if "4bit" in model_id else 9.0
        elif "9b" in model_id.lower() or "9B" in model_id:
            return 5.2 if "4bit" in model_id else 10.5
        elif "13b" in model_id.lower() or "13B" in model_id:
            return 7.5 if "4bit" in model_id else 15.0
        else:
            return 5.0  # Default estimate


# Singleton instance
download_manager = DownloadManager()