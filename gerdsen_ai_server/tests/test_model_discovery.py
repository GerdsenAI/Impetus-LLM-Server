"""
Unit tests for model discovery service — pure logic, no mocking required.
"""

import pytest
from src.services.model_discovery import ModelCategory, ModelDiscoveryService, ModelInfo


class TestModelDiscoveryService:
    """Tests for the ModelDiscoveryService catalog, search, filtering, and performance estimation."""

    @pytest.fixture
    def service(self):
        """Create a ModelDiscoveryService instance."""
        return ModelDiscoveryService()

    def test_catalog_initialized(self, service):
        """Verify the internal catalog contains exactly 9 curated models."""
        assert len(service.models) == 9

    def test_get_all_models(self, service):
        """get_all_models returns every model in the catalog."""
        models = service.get_all_models()
        assert len(models) == 9
        assert all(isinstance(m, ModelInfo) for m in models)

    def test_get_models_by_category_coding(self, service):
        """CODING category contains exactly 2 models (Qwen Coder + DeepSeek Coder)."""
        coding_models = service.get_models_by_category(ModelCategory.CODING)
        assert len(coding_models) == 2
        assert all(m.category == ModelCategory.CODING for m in coding_models)

    def test_get_models_by_category_empty(self, service):
        """MULTIMODAL category has no models in the current catalog."""
        multimodal_models = service.get_models_by_category(ModelCategory.MULTIMODAL)
        assert len(multimodal_models) == 0

    def test_get_recommended_4gb(self, service):
        """Only models with min_memory_gb <= 4 are returned for 4 GB available memory."""
        recommended = service.get_recommended_models(available_memory_gb=4.0)
        assert len(recommended) > 0
        assert all(m.min_memory_gb <= 4.0 for m in recommended)

    def test_get_recommended_with_use_case(self, service):
        """Filtering by 'programming' use case returns only coding-related models."""
        recommended = service.get_recommended_models(available_memory_gb=16.0, use_case="programming")
        assert len(recommended) > 0
        assert all("programming" in m.recommended_for for m in recommended)

    def test_get_recommended_returns_at_most_5(self, service):
        """Recommendations are capped at 5 results even when more models qualify."""
        recommended = service.get_recommended_models(available_memory_gb=64.0)
        assert len(recommended) <= 5

    def test_get_recommended_sorted_by_popularity(self, service):
        """Recommended models are sorted descending by popularity_score."""
        recommended = service.get_recommended_models(available_memory_gb=64.0)
        scores = [m.popularity_score for m in recommended]
        assert scores == sorted(scores, reverse=True)

    def test_search_by_name(self, service):
        """Searching 'mistral' returns models whose name or id contains 'mistral'."""
        results = service.search_models("mistral")
        assert len(results) > 0
        for m in results:
            assert "mistral" in m.name.lower() or "mistral" in m.id.lower()

    def test_search_by_feature(self, service):
        """Searching 'code-generation' returns coding models that list it as a feature."""
        results = service.search_models("code-generation")
        assert len(results) >= 2
        for m in results:
            assert "code-generation" in m.features

    def test_search_case_insensitive(self, service):
        """Search is case-insensitive — 'MISTRAL' matches lowercase catalog data."""
        results = service.search_models("MISTRAL")
        assert len(results) > 0

    def test_search_no_results(self, service):
        """Searching a term that matches nothing returns an empty list."""
        results = service.search_models("zzz-nonexistent-zzz")
        assert results == []

    def test_get_model_info_exists(self, service):
        """get_model_info returns a ModelInfo for a known model id."""
        model = service.get_model_info("mlx-community/Mistral-7B-Instruct-v0.3-4bit")
        assert model is not None
        assert isinstance(model, ModelInfo)
        assert model.name == "Mistral 7B Instruct v0.3"

    def test_get_model_info_not_found(self, service):
        """get_model_info returns None for an unknown model id."""
        model = service.get_model_info("nonexistent/model-id")
        assert model is None

    def test_estimate_performance_base(self, service):
        """Base M2 chip returns the raw tokens/sec from the performance dict."""
        model_id = "mlx-community/Mistral-7B-Instruct-v0.3-4bit"
        tps = service.estimate_performance(model_id, "m2")
        assert tps == 70

    def test_estimate_performance_pro(self, service):
        """M2 Pro applies a 1.1x multiplier to the base M2 performance."""
        model_id = "mlx-community/Mistral-7B-Instruct-v0.3-4bit"
        tps = service.estimate_performance(model_id, "m2 pro")
        assert tps == int(70 * 1.1)

    def test_estimate_performance_max(self, service):
        """M2 Max applies a 1.3x multiplier to the base M2 performance."""
        model_id = "mlx-community/Mistral-7B-Instruct-v0.3-4bit"
        tps = service.estimate_performance(model_id, "m2 max")
        assert tps == int(70 * 1.3)

    def test_estimate_performance_ultra(self, service):
        """M2 Ultra applies a 1.5x multiplier to the base M2 performance."""
        model_id = "mlx-community/Mistral-7B-Instruct-v0.3-4bit"
        tps = service.estimate_performance(model_id, "m2 ultra")
        assert tps == int(70 * 1.5)

    def test_estimate_performance_unknown_model(self, service):
        """estimate_performance returns None for a model id not in the catalog."""
        tps = service.estimate_performance("nonexistent/model-id", "m2")
        assert tps is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
