"""
Model warmup service for eliminating cold start latency
"""

import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

from loguru import logger

try:
    import mlx
    import mlx.core as mx
    from mlx_lm import generate
    MLX_AVAILABLE = True
except ImportError:
    MLX_AVAILABLE = False
    logger.warning("MLX not available for model warmup")

from ..config.settings import settings


@dataclass
class WarmupStatus:
    """Status of model warmup"""
    model_id: str
    is_warmed: bool = False
    warmup_time_ms: float = 0.0
    last_warmup: float | None = None
    warmup_prompts_used: int = 0
    kernel_compilation_time_ms: float = 0.0
    error: str | None = None


class ModelWarmupService:
    """
    Service for warming up models to eliminate cold start latency.
    
    Pre-compiles Metal kernels and runs inference passes to ensure
    optimal performance for the first real user request.
    """

    # Standard warmup prompts of varying lengths
    WARMUP_PROMPTS = [
        "Hello",  # Very short
        "The quick brown fox jumps over the lazy dog.",  # Medium
        "In the realm of artificial intelligence and machine learning, " +
        "the development of large language models has revolutionized " +
        "natural language processing tasks across various domains.",  # Long
    ]

    def __init__(self):
        """Initialize warmup service"""
        self.warmup_status: dict[str, WarmupStatus] = {}
        self.warmup_executor = ThreadPoolExecutor(max_workers=2)
        self._warmup_lock = threading.Lock()

        # Load cached warmup data if available
        self.cache_file = settings.model.cache_dir / "warmup_cache.json"
        self._load_cache()

    def _load_cache(self):
        """Load cached warmup information"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file) as f:
                    cache_data = json.load(f)
                    for model_id, data in cache_data.items():
                        self.warmup_status[model_id] = WarmupStatus(
                            model_id=model_id,
                            is_warmed=False,  # Always start cold
                            warmup_time_ms=data.get('warmup_time_ms', 0),
                            last_warmup=data.get('last_warmup'),
                            warmup_prompts_used=data.get('warmup_prompts_used', 0)
                        )
            except Exception as e:
                logger.warning(f"Failed to load warmup cache: {e}")

    def _save_cache(self):
        """Save warmup information to cache"""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_data = {}

            for model_id, status in self.warmup_status.items():
                if status.last_warmup:  # Only cache successful warmups
                    cache_data[model_id] = {
                        'warmup_time_ms': status.warmup_time_ms,
                        'last_warmup': status.last_warmup,
                        'warmup_prompts_used': status.warmup_prompts_used,
                        'kernel_compilation_time_ms': status.kernel_compilation_time_ms
                    }

            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save warmup cache: {e}")

    def warmup_model(self, model: Any, model_id: str,
                    num_prompts: int = 3,
                    async_warmup: bool = True) -> WarmupStatus:
        """
        Warm up a model by running inference on sample prompts.
        
        Args:
            model: The MLX model instance
            model_id: Model identifier
            num_prompts: Number of warmup prompts to use (1-3)
            async_warmup: Whether to run warmup asynchronously
            
        Returns:
            WarmupStatus object
        """
        if not MLX_AVAILABLE:
            return WarmupStatus(
                model_id=model_id,
                error="MLX not available"
            )

        # Check if already warming/warmed
        with self._warmup_lock:
            if model_id in self.warmup_status and self.warmup_status[model_id].is_warmed:
                logger.info(f"Model {model_id} is already warmed up")
                return self.warmup_status[model_id]

        if async_warmup:
            # Submit warmup task
            future = self.warmup_executor.submit(
                self._warmup_model_sync, model, model_id, num_prompts
            )

            # Create pending status
            status = WarmupStatus(model_id=model_id)
            self.warmup_status[model_id] = status

            # Update status when complete
            def update_status(f):
                try:
                    result = f.result()
                    self.warmup_status[model_id] = result
                    self._save_cache()
                except Exception as e:
                    logger.error(f"Warmup failed for {model_id}: {e}")
                    self.warmup_status[model_id].error = str(e)

            future.add_done_callback(update_status)
            return status
        else:
            # Synchronous warmup
            return self._warmup_model_sync(model, model_id, num_prompts)

    def _warmup_model_sync(self, model: Any, model_id: str, num_prompts: int) -> WarmupStatus:
        """Synchronously warm up a model"""
        logger.info(f"Starting warmup for model {model_id}")

        status = WarmupStatus(model_id=model_id)
        start_time = time.time()

        try:
            # Ensure we have required attributes
            if not hasattr(model, 'tokenizer_instance') or not hasattr(model, 'model_instance'):
                raise ValueError("Model missing required tokenizer or model instance")

            # Clear any existing Metal cache
            mx.metal.clear_cache()

            # Phase 1: Force kernel compilation with minimal inference
            kernel_start = time.time()

            # Use the shortest prompt for kernel compilation
            prompt = self.WARMUP_PROMPTS[0]
            logger.debug(f"Compiling kernels with prompt: '{prompt}'")

            # First inference triggers kernel compilation
            _ = generate(
                model.model_instance,
                model.tokenizer_instance,
                prompt=prompt,
                max_tokens=1,  # Minimal generation
                temperature=0.7,
                verbose=False
            )

            kernel_time = (time.time() - kernel_start) * 1000
            status.kernel_compilation_time_ms = kernel_time
            logger.info(f"Kernel compilation took {kernel_time:.1f}ms")

            # Phase 2: Run warmup prompts
            prompts_to_use = min(num_prompts, len(self.WARMUP_PROMPTS))

            for i in range(prompts_to_use):
                prompt = self.WARMUP_PROMPTS[i]
                prompt_start = time.time()

                # Generate with reasonable length
                response = generate(
                    model.model_instance,
                    model.tokenizer_instance,
                    prompt=prompt,
                    max_tokens=min(50, settings.inference.max_tokens),
                    temperature=0.7,
                    top_p=0.9,
                    verbose=False
                )

                prompt_time = (time.time() - prompt_start) * 1000
                logger.debug(f"Warmup prompt {i+1} took {prompt_time:.1f}ms, "
                           f"generated: {len(response.split())} words")

                status.warmup_prompts_used += 1

            # Calculate total warmup time
            total_time = (time.time() - start_time) * 1000
            status.warmup_time_ms = total_time
            status.is_warmed = True
            status.last_warmup = time.time()

            logger.info(f"Model {model_id} warmed up successfully in {total_time:.1f}ms "
                       f"(kernel: {kernel_time:.1f}ms, inference: {total_time - kernel_time:.1f}ms)")

            # Emit warmup complete event if WebSocket available
            self._emit_warmup_event(model_id, status)

            return status

        except Exception as e:
            logger.error(f"Warmup failed for {model_id}: {e}")
            status.error = str(e)
            status.warmup_time_ms = (time.time() - start_time) * 1000
            return status

    def get_warmup_status(self, model_id: str) -> WarmupStatus | None:
        """Get warmup status for a model"""
        return self.warmup_status.get(model_id)

    def is_model_warm(self, model_id: str) -> bool:
        """Check if a model is warmed up"""
        status = self.warmup_status.get(model_id)
        return status.is_warmed if status else False

    def clear_warmup_status(self, model_id: str):
        """Clear warmup status for a model"""
        if model_id in self.warmup_status:
            self.warmup_status[model_id].is_warmed = False
            logger.info(f"Cleared warmup status for {model_id}")

    def get_all_warmup_status(self) -> dict[str, dict[str, Any]]:
        """Get warmup status for all models"""
        result = {}

        for model_id, status in self.warmup_status.items():
            result[model_id] = {
                'is_warmed': status.is_warmed,
                'warmup_time_ms': status.warmup_time_ms,
                'last_warmup': status.last_warmup,
                'warmup_prompts_used': status.warmup_prompts_used,
                'kernel_compilation_time_ms': status.kernel_compilation_time_ms,
                'error': status.error,
                'age_seconds': (time.time() - status.last_warmup) if status.last_warmup else None
            }

        return result

    def benchmark_cold_vs_warm(self, model: Any, model_id: str) -> dict[str, Any]:
        """
        Benchmark cold vs warm inference performance.
        
        Returns detailed timing information comparing cold start vs warmed model.
        """
        if not MLX_AVAILABLE:
            return {'error': 'MLX not available'}

        logger.info(f"Starting cold vs warm benchmark for {model_id}")

        # Test prompt
        test_prompt = "Write a short story about a robot learning to paint."
        max_tokens = 100

        try:
            # Step 1: Cold start benchmark
            mx.metal.clear_cache()  # Ensure cold start

            cold_start = time.time()
            cold_first_token_time = None

            # Generate and measure first token time
            response_generator = generate(
                model.model_instance,
                model.tokenizer_instance,
                prompt=test_prompt,
                max_tokens=max_tokens,
                temperature=0.7,
                verbose=False
            )

            # Time to first token (approximate)
            cold_inference_start = time.time()
            if isinstance(response_generator, str):
                # Non-streaming response
                cold_response = response_generator
                cold_first_token_time = (time.time() - cold_inference_start) * 1000
            else:
                # Streaming response - measure first token
                cold_response = ""
                for i, token in enumerate(response_generator):
                    if i == 0:
                        cold_first_token_time = (time.time() - cold_inference_start) * 1000
                    cold_response += token

            cold_total_time = (time.time() - cold_start) * 1000

            # Step 2: Warm up the model
            warmup_status = self._warmup_model_sync(model, model_id, 3)

            # Step 3: Warm benchmark
            warm_start = time.time()
            warm_first_token_time = None

            response_generator = generate(
                model.model_instance,
                model.tokenizer_instance,
                prompt=test_prompt,
                max_tokens=max_tokens,
                temperature=0.7,
                verbose=False
            )

            warm_inference_start = time.time()
            if isinstance(response_generator, str):
                warm_response = response_generator
                warm_first_token_time = (time.time() - warm_inference_start) * 1000
            else:
                warm_response = ""
                for i, token in enumerate(response_generator):
                    if i == 0:
                        warm_first_token_time = (time.time() - warm_inference_start) * 1000
                    warm_response += token

            warm_total_time = (time.time() - warm_start) * 1000

            # Calculate improvements
            first_token_improvement = ((cold_first_token_time - warm_first_token_time) /
                                     cold_first_token_time * 100) if cold_first_token_time else 0
            total_improvement = ((cold_total_time - warm_total_time) /
                               cold_total_time * 100) if cold_total_time else 0

            results = {
                'model_id': model_id,
                'cold_start': {
                    'first_token_ms': cold_first_token_time,
                    'total_time_ms': cold_total_time,
                    'tokens_generated': len(cold_response.split())
                },
                'warm_start': {
                    'first_token_ms': warm_first_token_time,
                    'total_time_ms': warm_total_time,
                    'tokens_generated': len(warm_response.split()),
                    'warmup_time_ms': warmup_status.warmup_time_ms
                },
                'improvement': {
                    'first_token_percent': first_token_improvement,
                    'total_time_percent': total_improvement,
                    'first_token_speedup': cold_first_token_time / warm_first_token_time if warm_first_token_time else 0
                }
            }

            logger.info(f"Benchmark complete: {first_token_improvement:.1f}% first token improvement")

            return results

        except Exception as e:
            logger.error(f"Benchmark failed: {e}")
            return {'error': str(e)}

    def _emit_warmup_event(self, model_id: str, status: WarmupStatus):
        """Emit warmup event via WebSocket if available"""
        try:
            from flask import current_app
            app_state = current_app.config.get('app_state', {})
            socketio = app_state.get('socketio')

            if socketio:
                socketio.emit('model_warmup_complete', {
                    'model_id': model_id,
                    'warmup_time_ms': status.warmup_time_ms,
                    'kernel_compilation_time_ms': status.kernel_compilation_time_ms,
                    'is_warmed': status.is_warmed,
                    'error': status.error
                })
        except Exception as e:
            logger.debug(f"Could not emit warmup event: {e}")

    def shutdown(self):
        """Shutdown warmup service"""
        logger.info("Shutting down warmup service")
        self.warmup_executor.shutdown(wait=True)
        self._save_cache()


# Global warmup service instance
model_warmup_service = ModelWarmupService()
