"""
Unit tests for model warmup service
"""

import threading
import time
from unittest.mock import MagicMock, patch

import pytest
from src.services.model_warmup import ModelWarmupService, WarmupStatus


class TestWarmupStatus:
    """Test WarmupStatus dataclass"""

    def test_warmup_status_creation(self):
        """Test creating warmup status"""
        status = WarmupStatus(model_id="test-model")

        assert status.model_id == "test-model"
        assert not status.is_warmed
        assert status.warmup_time_ms == 0.0
        assert status.last_warmup is None
        assert status.warmup_prompts_used == 0
        assert status.kernel_compilation_time_ms == 0.0
        assert status.error is None


class TestModelWarmupService:
    """Test model warmup service"""

    @pytest.fixture
    def warmup_service(self, tmp_path):
        """Create test warmup service with temp cache"""
        with patch('src.services.model_warmup.settings') as mock_settings:
            mock_settings.model.cache_dir = tmp_path
            mock_settings.inference.max_tokens = 100
            service = ModelWarmupService()
            yield service
            service.shutdown()

    @pytest.fixture
    def mock_model(self):
        """Create mock MLX model"""
        model = MagicMock()
        model.model_id = "test-model"
        model.model_instance = MagicMock()
        model.tokenizer_instance = MagicMock()
        return model

    def test_warmup_service_init(self, warmup_service):
        """Test service initialization"""
        assert len(warmup_service.warmup_status) == 0
        assert warmup_service.warmup_executor is not None
        assert warmup_service._warmup_lock is not None

    @patch('src.services.model_warmup.MLX_AVAILABLE', False)
    def test_warmup_without_mlx(self, warmup_service, mock_model):
        """Test warmup when MLX is not available"""
        status = warmup_service.warmup_model(mock_model, "test-model", async_warmup=False)

        assert status.model_id == "test-model"
        assert not status.is_warmed
        assert status.error == "MLX not available"

    @patch('src.services.model_warmup.MLX_AVAILABLE', True)
    @patch('src.services.model_warmup.generate')
    @patch('src.services.model_warmup.mx')
    def test_synchronous_warmup(self, mock_mx, mock_generate, warmup_service, mock_model):
        """Test synchronous model warmup"""
        # Mock generate function
        mock_generate.return_value = "Generated text response"

        # Perform warmup
        status = warmup_service.warmup_model(
            mock_model,
            "test-model",
            num_prompts=2,
            async_warmup=False
        )

        # Verify warmup was successful
        assert status.model_id == "test-model"
        assert status.is_warmed
        assert status.warmup_time_ms > 0
        assert status.kernel_compilation_time_ms > 0
        assert status.warmup_prompts_used == 2
        assert status.last_warmup is not None
        assert status.error is None

        # Verify MLX calls
        mock_mx.metal.clear_cache.assert_called_once()
        # Should be called 3 times: 1 for kernel compilation + 2 warmup prompts
        assert mock_generate.call_count == 3

    @patch('src.services.model_warmup.MLX_AVAILABLE', True)
    @patch('src.services.model_warmup.generate')
    @patch('src.services.model_warmup.mx')
    def test_asynchronous_warmup(self, mock_mx, mock_generate, warmup_service, mock_model):
        """Test asynchronous model warmup"""
        mock_generate.return_value = "Generated text"

        # Start async warmup
        status = warmup_service.warmup_model(
            mock_model,
            "test-model",
            num_prompts=1,
            async_warmup=True
        )

        # Initial status should show not warmed
        assert status.model_id == "test-model"
        assert not status.is_warmed

        # Wait for async warmup to complete
        time.sleep(2.0)

        # Check updated status
        updated_status = warmup_service.get_warmup_status("test-model")
        assert updated_status.is_warmed
        assert updated_status.warmup_time_ms > 0

    def test_get_warmup_status(self, warmup_service):
        """Test getting warmup status"""
        # No status initially
        status = warmup_service.get_warmup_status("unknown-model")
        assert status is None

        # Add a status
        test_status = WarmupStatus(
            model_id="test-model",
            is_warmed=True,
            warmup_time_ms=100.0
        )
        warmup_service.warmup_status["test-model"] = test_status

        # Get status
        retrieved = warmup_service.get_warmup_status("test-model")
        assert retrieved == test_status

    def test_is_model_warm(self, warmup_service):
        """Test checking if model is warm"""
        assert not warmup_service.is_model_warm("unknown-model")

        # Add warmed model
        warmup_service.warmup_status["warm-model"] = WarmupStatus(
            model_id="warm-model",
            is_warmed=True
        )

        # Add cold model
        warmup_service.warmup_status["cold-model"] = WarmupStatus(
            model_id="cold-model",
            is_warmed=False
        )

        assert warmup_service.is_model_warm("warm-model")
        assert not warmup_service.is_model_warm("cold-model")

    def test_clear_warmup_status(self, warmup_service):
        """Test clearing warmup status"""
        # Add warmed model
        warmup_service.warmup_status["test-model"] = WarmupStatus(
            model_id="test-model",
            is_warmed=True
        )

        # Clear status
        warmup_service.clear_warmup_status("test-model")

        # Should still exist but not be warmed
        status = warmup_service.get_warmup_status("test-model")
        assert status is not None
        assert not status.is_warmed

    def test_get_all_warmup_status(self, warmup_service):
        """Test getting all warmup statuses"""
        # Add multiple models
        warmup_service.warmup_status["model1"] = WarmupStatus(
            model_id="model1",
            is_warmed=True,
            warmup_time_ms=100.0,
            last_warmup=time.time()
        )

        warmup_service.warmup_status["model2"] = WarmupStatus(
            model_id="model2",
            is_warmed=False,
            error="Test error"
        )

        # Get all status
        all_status = warmup_service.get_all_warmup_status()

        assert len(all_status) == 2
        assert all_status["model1"]["is_warmed"]
        assert all_status["model1"]["warmup_time_ms"] == 100.0
        assert all_status["model1"]["age_seconds"] is not None

        assert not all_status["model2"]["is_warmed"]
        assert all_status["model2"]["error"] == "Test error"

    @patch('src.services.model_warmup.MLX_AVAILABLE', True)
    @patch('src.services.model_warmup.generate')
    @patch('src.services.model_warmup.mx')
    def test_benchmark_cold_vs_warm(self, mock_mx, mock_generate, warmup_service, mock_model):
        """Test cold vs warm benchmarking"""
        # Mock different response times
        call_count = 0

        def mock_generate_impl(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # Simulate slower first call (cold)
            if call_count <= 2:  # First benchmark calls
                time.sleep(0.1)
            else:  # Warm calls
                time.sleep(0.01)
            return "Generated response with multiple tokens for testing"

        mock_generate.side_effect = mock_generate_impl

        # Run benchmark
        results = warmup_service.benchmark_cold_vs_warm(mock_model, "test-model")

        # Verify results structure
        assert "model_id" in results
        assert results["model_id"] == "test-model"

        assert "cold_start" in results
        assert results["cold_start"]["first_token_ms"] is not None
        assert results["cold_start"]["total_time_ms"] > 0

        assert "warm_start" in results
        assert results["warm_start"]["first_token_ms"] is not None
        assert results["warm_start"]["total_time_ms"] > 0

        assert "improvement" in results
        # total_time_percent is reliable (captures full generate duration)
        # first_token_percent is unreliable with non-streaming mocks (near-zero durations)
        assert results["improvement"]["total_time_percent"] > 0

    def test_cache_persistence(self, tmp_path):
        """Test warmup cache persistence"""
        # Create service with cache
        with patch('src.services.model_warmup.settings') as mock_settings:
            mock_settings.model.cache_dir = tmp_path

            # First service instance
            service1 = ModelWarmupService()
            service1.warmup_status["model1"] = WarmupStatus(
                model_id="model1",
                is_warmed=True,
                warmup_time_ms=150.0,
                last_warmup=time.time()
            )
            service1._save_cache()
            service1.shutdown()

            # Second service instance should load cache
            service2 = ModelWarmupService()

            # Should have loaded the cached data
            assert "model1" in service2.warmup_status
            assert service2.warmup_status["model1"].warmup_time_ms == 150.0
            # Should start cold though
            assert not service2.warmup_status["model1"].is_warmed

            service2.shutdown()

    @patch('src.services.model_warmup.MLX_AVAILABLE', True)
    @patch('src.services.model_warmup.generate')
    def test_warmup_error_handling(self, mock_generate, warmup_service, mock_model):
        """Test warmup error handling"""
        # Make generate raise an error
        mock_generate.side_effect = RuntimeError("Test generation error")

        # Attempt warmup
        status = warmup_service.warmup_model(
            mock_model,
            "test-model",
            async_warmup=False
        )

        # Should capture error
        assert not status.is_warmed
        assert status.error == "Test generation error"
        assert status.warmup_time_ms > 0  # Should still track time

    def test_concurrent_warmup(self, warmup_service):
        """Test concurrent warmup requests"""
        # This tests thread safety
        results = []

        def warmup_task(model_id):
            status = WarmupStatus(model_id=model_id, is_warmed=True)
            warmup_service.warmup_status[model_id] = status
            results.append(model_id)

        # Start multiple threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=warmup_task, args=(f"model-{i}",))
            threads.append(t)
            t.start()

        # Wait for completion
        for t in threads:
            t.join()

        # All should complete successfully
        assert len(results) == 5
        assert len(warmup_service.warmup_status) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
