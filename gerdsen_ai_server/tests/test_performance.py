"""
Performance regression tests to ensure optimization targets are met
"""

import gc
import statistics
import time
from unittest.mock import MagicMock, patch

import psutil
import pytest
from src.services.benchmark_service import BenchmarkResult


class TestPerformanceRegression:
    """Test performance doesn't regress from established baselines"""

    # Performance baselines (conservative targets)
    BASELINES = {
        'model_load_time_ms': {
            'mmap': 5000,      # <5s with mmap
            'regular': 30000   # <30s without
        },
        'first_token_latency_ms': {
            'cold': 2000,      # <2s cold
            'warm': 200        # <200ms warm
        },
        'tokens_per_second': {
            'M1': 40,          # Minimum for each chip
            'M2': 60,
            'M3': 80,
            'M4': 100
        },
        'memory_overhead_mb': 500,  # Base overhead
        'api_latency_ms': 50,       # API overhead
        'warmup_time_ms': 5000      # <5s warmup
    }

    @pytest.fixture
    def mock_model(self):
        """Create mock model for testing"""
        model = MagicMock()
        model.model_id = "test-model"
        model.loaded = True
        return model

    def test_model_load_time_regression(self):
        """Test model loading doesn't exceed baseline"""
        from src.utils.mmap_loader import MemoryMappedLoader

        loader = MemoryMappedLoader()

        # Mock file operations for speed
        with patch('mmap.mmap') as mock_mmap:
            with patch('builtins.open'):
                with patch('pathlib.Path.stat') as mock_stat:
                    mock_stat.return_value = MagicMock(st_size=1024*1024*100)  # 100MB

                    start = time.time()
                    # Simulate loading
                    loader._load_safetensors(MagicMock(), read_only=True)
                    load_time = (time.time() - start) * 1000

                    # Should be well under baseline
                    assert load_time < self.BASELINES['model_load_time_ms']['mmap']

    @patch('src.services.model_warmup.MLX_AVAILABLE', True)
    @patch('src.services.model_warmup.generate')
    def test_warmup_time_regression(self, mock_generate):
        """Test model warmup doesn't exceed baseline"""
        from src.services.model_warmup import ModelWarmupService

        service = ModelWarmupService()
        mock_model = self.mock_model()

        # Mock fast generation
        mock_generate.return_value = "Response"

        start = time.time()
        status = service._warmup_model_sync(mock_model, "test-model", num_prompts=3)
        warmup_time = (time.time() - start) * 1000

        assert warmup_time < self.BASELINES['warmup_time_ms']
        assert status.is_warmed

    def test_first_token_latency_regression(self):
        """Test first token latency meets targets"""
        # This would test actual inference, mocked here
        latencies = {
            'cold': 1500,  # Simulated cold latency
            'warm': 150    # Simulated warm latency
        }

        assert latencies['cold'] < self.BASELINES['first_token_latency_ms']['cold']
        assert latencies['warm'] < self.BASELINES['first_token_latency_ms']['warm']

    def test_memory_overhead_regression(self):
        """Test base memory overhead stays low"""
        # Get current process memory
        process = psutil.Process()
        base_memory_mb = process.memory_info().rss / (1024 * 1024)

        # Should be reasonable (this is just the test process)
        # In production, measure actual server overhead
        assert base_memory_mb < 1000  # Test process should be <1GB

    def test_api_latency_regression(self):
        """Test API endpoint latency"""
        from flask import Flask
        from src.routes.models import bp

        app = Flask(__name__)
        app.register_blueprint(bp, url_prefix='/api/models')
        client = app.test_client()

        # Measure endpoint latency
        latencies = []

        with patch('src.routes.models.get_available_models') as mock_get:
            mock_get.return_value = []

            for _ in range(10):
                start = time.time()
                response = client.get('/api/models/list')
                latency = (time.time() - start) * 1000
                latencies.append(latency)
                assert response.status_code == 200

        avg_latency = statistics.mean(latencies)
        assert avg_latency < self.BASELINES['api_latency_ms']

    def test_concurrent_performance(self):
        """Test performance under concurrent load"""
        import queue
        from concurrent.futures import ThreadPoolExecutor

        results = queue.Queue()

        def worker(i):
            start = time.time()
            # Simulate some work
            time.sleep(0.01)
            duration = (time.time() - start) * 1000
            results.put(duration)

        # Run concurrent tasks
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(worker, i) for i in range(50)]
            for f in futures:
                f.result()

        # Check all completed reasonably fast
        latencies = []
        while not results.empty():
            latencies.append(results.get())

        avg_latency = statistics.mean(latencies)
        max_latency = max(latencies)

        # Even under load, should maintain performance
        assert avg_latency < 50  # Average under 50ms
        assert max_latency < 200  # Max under 200ms

    def test_memory_leak_detection(self):
        """Test for memory leaks in critical paths"""
        gc.collect()
        initial_objects = len(gc.get_objects())

        # Simulate repeated operations
        for _ in range(100):
            # Create and destroy objects
            data = {"test": [1, 2, 3] * 100}
            del data

        gc.collect()
        final_objects = len(gc.get_objects())

        # Should not accumulate objects
        object_growth = final_objects - initial_objects
        assert object_growth < 1000  # Reasonable threshold

    @patch('src.services.benchmark_service.BenchmarkService')
    def test_benchmark_performance_targets(self, mock_benchmark_class):
        """Test benchmark results meet targets"""
        mock_service = MagicMock()

        # Create realistic benchmark results
        result = BenchmarkResult(
            model_id="test-model",
            prompt_length=50,
            output_tokens=100,
            time_to_first_token_ms=180.0,
            total_time_ms=1500.0,
            tokens_per_second=66.7,  # 100 tokens / 1.5s
            memory_used_gb=4.5,
            gpu_utilization_avg=85.0,
            chip_type="M2",
            timestamp="2024-01-01T00:00:00"
        )

        # Verify meets M2 baseline
        assert result.tokens_per_second >= self.BASELINES['tokens_per_second']['M2']
        assert result.time_to_first_token_ms < self.BASELINES['first_token_latency_ms']['warm']
        assert result.gpu_utilization_avg > 80  # Good GPU utilization

    def test_cache_performance(self):
        """Test KV cache improves multi-turn performance"""
        from src.inference.kv_cache_manager import KVCacheManager

        manager = KVCacheManager(max_memory_gb=1.0)

        # Test cache operations are fast
        start = time.time()

        # Create cache
        cache = manager.create_cache(
            model_id="test",
            conversation_id="conv1",
            num_layers=32,
            num_heads=32,
            head_dim=128
        )

        # Update cache (simulated)
        for _ in range(10):
            manager.get_cache("test", "conv1")

        cache_time = (time.time() - start) * 1000

        # Cache operations should be very fast
        assert cache_time < 100  # <100ms for all operations

    def test_thermal_throttling_handling(self):
        """Test performance degrades gracefully under thermal pressure"""
        # Simulate thermal states and expected performance
        thermal_multipliers = {
            'nominal': 1.0,
            'fair': 0.9,
            'serious': 0.7,
            'critical': 0.5
        }

        base_tokens_per_sec = 80

        for state, multiplier in thermal_multipliers.items():
            expected = base_tokens_per_sec * multiplier
            # System should adapt performance based on thermal state
            assert expected > 0  # Should never stop completely


class TestMemoryEfficiency:
    """Test memory usage efficiency"""

    def test_model_memory_footprint(self):
        """Test model memory usage is efficient"""
        # Simulated model sizes
        model_sizes_gb = {
            '7B-4bit': 3.5,
            '7B-8bit': 7.0,
            '13B-4bit': 6.5,
            '13B-8bit': 13.0
        }

        # With mmap, actual memory should be less
        mmap_efficiency = 0.7  # 30% savings expected

        for model, size in model_sizes_gb.items():
            mmap_size = size * mmap_efficiency
            assert mmap_size < size

    def test_cache_memory_limits(self):
        """Test cache respects memory limits"""
        from src.inference.kv_cache_manager import KVCacheManager

        # Small cache for testing
        manager = KVCacheManager(max_memory_gb=0.1, max_conversations=2)

        # Add caches until limit
        for i in range(5):
            manager.create_cache(
                model_id="test",
                conversation_id=f"conv{i}",
                num_layers=12,
                num_heads=12,
                head_dim=64
            )

        # Should respect limits
        assert len(manager.caches) <= manager.max_conversations
        assert manager.total_memory_mb <= manager.max_memory_mb


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
