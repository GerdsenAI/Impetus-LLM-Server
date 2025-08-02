"""
Error Recovery and Resilience System
Handles failures gracefully and provides recovery mechanisms
"""

import time
import psutil
import functools
from typing import Callable, Optional, Any, Dict
from dataclasses import dataclass
from enum import Enum
from loguru import logger
import threading
from collections import deque
from datetime import datetime, timedelta


class ErrorType(Enum):
    """Types of errors we handle"""
    OUT_OF_MEMORY = "out_of_memory"
    THERMAL_THROTTLE = "thermal_throttle"
    MODEL_LOAD_FAILURE = "model_load_failure"
    DOWNLOAD_FAILURE = "download_failure"
    INFERENCE_FAILURE = "inference_failure"
    NETWORK_ERROR = "network_error"
    UNKNOWN = "unknown"


@dataclass
class ErrorEvent:
    """Record of an error event"""
    error_type: ErrorType
    timestamp: datetime
    message: str
    context: Dict[str, Any]
    recovered: bool = False


class ErrorRecoveryService:
    """Centralized error recovery and resilience"""
    
    def __init__(self, max_history: int = 100):
        self.error_history = deque(maxlen=max_history)
        self.recovery_strategies = {
            ErrorType.OUT_OF_MEMORY: self._recover_from_oom,
            ErrorType.THERMAL_THROTTLE: self._recover_from_thermal,
            ErrorType.MODEL_LOAD_FAILURE: self._recover_from_model_load_failure,
            ErrorType.DOWNLOAD_FAILURE: self._recover_from_download_failure,
            ErrorType.INFERENCE_FAILURE: self._recover_from_inference_failure,
            ErrorType.NETWORK_ERROR: self._recover_from_network_error,
        }
        self.app_state = None
    
    def set_app_state(self, app_state: Dict):
        """Set the Flask app state for recovery operations"""
        self.app_state = app_state
    
    def handle_error(self, error_type: ErrorType, error: Exception, 
                    context: Optional[Dict] = None) -> bool:
        """Handle an error and attempt recovery"""
        context = context or {}
        
        # Record the error
        event = ErrorEvent(
            error_type=error_type,
            timestamp=datetime.now(),
            message=str(error),
            context=context
        )
        self.error_history.append(event)
        
        logger.error(f"Error occurred: {error_type.value} - {error}")
        
        # Check if we're in a failure loop
        if self._is_failure_loop(error_type):
            logger.error(f"Failure loop detected for {error_type.value}, not attempting recovery")
            return False
        
        # Attempt recovery
        recovery_strategy = self.recovery_strategies.get(error_type)
        if recovery_strategy:
            try:
                success = recovery_strategy(error, context)
                event.recovered = success
                if success:
                    logger.info(f"Successfully recovered from {error_type.value}")
                else:
                    logger.warning(f"Recovery failed for {error_type.value}")
                return success
            except Exception as e:
                logger.error(f"Recovery strategy failed: {e}")
                return False
        
        return False
    
    def _is_failure_loop(self, error_type: ErrorType, 
                        window_minutes: int = 5, threshold: int = 3) -> bool:
        """Check if we're in a failure loop for this error type"""
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
        recent_errors = [
            e for e in self.error_history 
            if e.error_type == error_type and e.timestamp > cutoff_time
        ]
        return len(recent_errors) >= threshold
    
    def _recover_from_oom(self, error: Exception, context: Dict) -> bool:
        """Recover from out of memory error"""
        if not self.app_state:
            return False
        
        logger.info("Attempting OOM recovery...")
        
        # 1. Force garbage collection
        import gc
        gc.collect()
        
        # 2. Clear MLX cache if available
        try:
            import mlx.core as mx
            mx.metal.clear_cache()
            logger.info("Cleared MLX Metal cache")
        except:
            pass
        
        # 3. Unload least recently used model
        loaded_models = self.app_state.get('loaded_models', {})
        if loaded_models:
            # Simple LRU: unload first model (should track usage properly)
            model_to_unload = list(loaded_models.keys())[0]
            try:
                model = loaded_models.pop(model_to_unload)
                if hasattr(model, 'unload'):
                    model.unload()
                gc.collect()
                logger.info(f"Unloaded model {model_to_unload} to free memory")
                
                # Emit event if socketio available
                socketio = self.app_state.get('socketio')
                if socketio:
                    socketio.emit('model_unloaded', {
                        'model_id': model_to_unload,
                        'reason': 'out_of_memory_recovery'
                    }, room='models')
                
                return True
            except Exception as e:
                logger.error(f"Failed to unload model: {e}")
        
        return False
    
    def _recover_from_thermal(self, error: Exception, context: Dict) -> bool:
        """Recover from thermal throttling"""
        logger.info("Thermal throttling detected, switching to efficiency mode")
        
        if self.app_state:
            # Switch to efficiency mode
            from ..config.settings import settings
            settings.hardware.performance_mode = "efficiency"
            settings.hardware.max_cpu_percent = 60.0
            settings.hardware.max_memory_percent = 70.0
            
            # Reduce inference settings
            settings.inference.max_batch_size = 1
            settings.inference.max_tokens = min(settings.inference.max_tokens, 512)
            
            # Add cooldown period
            time.sleep(5)
            
            return True
        
        return False
    
    def _recover_from_model_load_failure(self, error: Exception, context: Dict) -> bool:
        """Recover from model loading failure"""
        model_id = context.get('model_id')
        if not model_id:
            return False
        
        logger.info(f"Attempting to recover from model load failure for {model_id}")
        
        # Clear any partial state
        import gc
        gc.collect()
        
        # Check if it's a path issue
        from pathlib import Path
        from ..config.settings import settings
        
        model_path = settings.model.models_dir / model_id.replace('/', '_')
        if not model_path.exists():
            logger.error(f"Model path does not exist: {model_path}")
            # Could trigger re-download here
            return False
        
        # Try with reduced settings
        logger.info("Retrying with reduced memory settings")
        return False  # Let caller retry with different settings
    
    def _recover_from_download_failure(self, error: Exception, context: Dict) -> bool:
        """Recover from download failure"""
        # Download manager already has retry logic
        # This is for additional recovery
        
        # Check if it's a disk space issue
        import shutil
        disk_usage = shutil.disk_usage('/')
        free_gb = disk_usage.free / (1024 ** 3)
        
        if free_gb < 5:  # Less than 5GB free
            logger.warning(f"Low disk space: {free_gb:.1f}GB free")
            # Could clean up cache here
            return False
        
        # Network issues are handled by download manager retries
        return False
    
    def _recover_from_inference_failure(self, error: Exception, context: Dict) -> bool:
        """Recover from inference failure"""
        logger.info("Attempting inference failure recovery")
        
        # Reduce inference parameters
        if "out of memory" in str(error).lower():
            # Reduce context window
            from ..config.settings import settings
            settings.inference.max_tokens = min(settings.inference.max_tokens // 2, 256)
            logger.info(f"Reduced max_tokens to {settings.inference.max_tokens}")
            return True
        
        return False
    
    def _recover_from_network_error(self, error: Exception, context: Dict) -> bool:
        """Recover from network errors"""
        # Most network recovery is handled by retry decorators
        # This is for system-level recovery
        logger.info("Network error detected, will retry with backoff")
        return True


def with_error_recovery(error_type: ErrorType, max_retries: int = 3, 
                       backoff_factor: float = 2.0):
    """Decorator for automatic error recovery with retries"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    
                    # Get recovery service
                    from . import error_recovery_service
                    
                    # Build context
                    context = {
                        'function': func.__name__,
                        'attempt': attempt + 1,
                        'args': str(args)[:100],  # Truncate for safety
                        'kwargs': str(kwargs)[:100]
                    }
                    
                    # Attempt recovery
                    recovered = error_recovery_service.handle_error(
                        error_type, e, context
                    )
                    
                    if not recovered and attempt < max_retries - 1:
                        # Exponential backoff
                        wait_time = backoff_factor ** attempt
                        logger.info(f"Retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                    elif not recovered:
                        # Final attempt failed
                        raise
            
            # All retries exhausted
            raise last_error
        
        return wrapper
    return decorator


def with_memory_limit(max_memory_gb: float):
    """Decorator to enforce memory limits on functions"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Check memory before execution
            memory = psutil.virtual_memory()
            used_gb = memory.used / (1024 ** 3)
            
            if used_gb > max_memory_gb:
                raise MemoryError(f"Memory usage {used_gb:.1f}GB exceeds limit {max_memory_gb}GB")
            
            # Execute with monitoring
            result = func(*args, **kwargs)
            
            # Check memory after
            memory_after = psutil.virtual_memory()
            used_after_gb = memory_after.used / (1024 ** 3)
            
            if used_after_gb > max_memory_gb * 1.1:  # 10% grace
                logger.warning(f"Function {func.__name__} exceeded memory limit: {used_after_gb:.1f}GB")
            
            return result
        
        return wrapper
    return decorator


# Singleton instance
error_recovery_service = ErrorRecoveryService()