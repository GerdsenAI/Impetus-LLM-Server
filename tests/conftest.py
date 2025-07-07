"""
Common pytest fixtures for Impetus LLM Server tests
"""

import os
import sys
import pytest
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import components for fixtures
from gerdsen_ai_server.src.inference import (
    GGUFInferenceEngine,
    GenerationConfig,
    get_inference_engine
)
from gerdsen_ai_server.src.enhanced_apple_silicon_detector import EnhancedAppleSiliconDetector
from gerdsen_ai_server.src.apple_frameworks_integration import AppleFrameworksIntegration
from gerdsen_ai_server.src.integrated_mlx_manager import IntegratedMLXManager
from gerdsen_ai_server.src.production_gerdsen_ai import (
    ProductionGerdsenAI, 
    ProductionConfig, 
    RealTimeMetricsCollector
)

@pytest.fixture
def test_model_info():
    """Test model information fixture"""
    return {
        'name': 'test-model',
        'architecture': 'llama',
        'context_length': 2048,
        'embedding_length': 4096,
        'n_layers': 32,
        'quantization': 'Q4_K_M'
    }

@pytest.fixture
def gguf_engine():
    """Create a fresh GGUF inference engine"""
    return GGUFInferenceEngine()

@pytest.fixture
def apple_detector():
    """Create Apple Silicon detector"""
    return EnhancedAppleSiliconDetector()

@pytest.fixture
def apple_frameworks():
    """Create Apple frameworks integration"""
    return AppleFrameworksIntegration()

@pytest.fixture
def mlx_manager():
    """Create MLX manager"""
    return IntegratedMLXManager()

@pytest.fixture
def production_config():
    """Create production configuration"""
    return ProductionConfig()

@pytest.fixture
def metrics_collector():
    """Create metrics collector"""
    return RealTimeMetricsCollector()

@pytest.fixture
def production_app():
    """Create production application"""
    return ProductionGerdsenAI()
