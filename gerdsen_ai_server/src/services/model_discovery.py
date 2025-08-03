"""
Model Discovery Service - Curated list of high-quality MLX models
"""

from dataclasses import dataclass
from enum import Enum

from loguru import logger


class ModelCategory(Enum):
    GENERAL = "general"
    CODING = "coding"
    CHAT = "chat"
    EFFICIENT = "efficient"
    MULTIMODAL = "multimodal"
    SPECIALIZED = "specialized"


@dataclass
class ModelInfo:
    """Model information with performance characteristics"""
    id: str
    name: str
    category: ModelCategory
    size_gb: float
    quantization: str
    context_length: int
    description: str
    performance: dict[str, int]  # chip_type -> tokens_per_sec
    features: list[str]
    recommended_for: list[str]
    min_memory_gb: float
    popularity_score: float  # 0-10 rating


class ModelDiscoveryService:
    """Service for discovering and recommending MLX models"""

    def __init__(self):
        self.models = self._initialize_model_catalog()
        logger.info(f"Model discovery service initialized with {len(self.models)} models")

    def _initialize_model_catalog(self) -> list[ModelInfo]:
        """Initialize the curated model catalog"""
        return [
            # General Purpose Models
            ModelInfo(
                id="mlx-community/Mistral-7B-Instruct-v0.3-4bit",
                name="Mistral 7B Instruct v0.3",
                category=ModelCategory.GENERAL,
                size_gb=3.8,
                quantization="4-bit",
                context_length=32768,
                description="Excellent general-purpose model with strong instruction following",
                performance={"m1": 50, "m2": 70, "m3": 90, "m4": 110},
                features=["instruction-following", "multi-turn-conversation", "reasoning"],
                recommended_for=["general-qa", "assistant", "analysis"],
                min_memory_gb=8.0,
                popularity_score=9.5
            ),
            ModelInfo(
                id="mlx-community/Mistral-7B-Instruct-v0.3-8bit",
                name="Mistral 7B Instruct v0.3 (8-bit)",
                category=ModelCategory.GENERAL,
                size_gb=7.5,
                quantization="8-bit",
                context_length=32768,
                description="Higher precision version for quality-critical tasks",
                performance={"m1": 40, "m2": 55, "m3": 70, "m4": 85},
                features=["high-precision", "instruction-following", "analysis"],
                recommended_for=["research", "detailed-analysis", "quality-critical"],
                min_memory_gb=12.0,
                popularity_score=8.5
            ),

            # Efficient Models
            ModelInfo(
                id="mlx-community/Llama-3.2-3B-Instruct-4bit",
                name="Llama 3.2 3B Instruct",
                category=ModelCategory.EFFICIENT,
                size_gb=1.8,
                quantization="4-bit",
                context_length=8192,
                description="Fast and efficient model, great for quick responses",
                performance={"m1": 80, "m2": 110, "m3": 140, "m4": 170},
                features=["fast-inference", "low-memory", "instruction-following"],
                recommended_for=["quick-tasks", "low-memory-devices", "high-throughput"],
                min_memory_gb=4.0,
                popularity_score=9.0
            ),
            ModelInfo(
                id="mlx-community/Phi-3.5-mini-instruct-4bit",
                name="Phi 3.5 Mini Instruct",
                category=ModelCategory.EFFICIENT,
                size_gb=2.2,
                quantization="4-bit",
                context_length=128000,
                description="Microsoft's efficient model with impressive long context",
                performance={"m1": 75, "m2": 100, "m3": 125, "m4": 150},
                features=["long-context", "efficient", "reasoning"],
                recommended_for=["document-analysis", "long-conversations", "efficiency"],
                min_memory_gb=4.0,
                popularity_score=8.8
            ),

            # Coding Models
            ModelInfo(
                id="mlx-community/Qwen2.5-Coder-7B-Instruct-4bit",
                name="Qwen 2.5 Coder 7B",
                category=ModelCategory.CODING,
                size_gb=4.2,
                quantization="4-bit",
                context_length=32768,
                description="State-of-the-art coding model with excellent completion",
                performance={"m1": 45, "m2": 65, "m3": 85, "m4": 100},
                features=["code-generation", "debugging", "code-review", "multi-language"],
                recommended_for=["programming", "code-review", "debugging"],
                min_memory_gb=8.0,
                popularity_score=9.7
            ),
            ModelInfo(
                id="mlx-community/DeepSeek-Coder-V2-Lite-Instruct-4bit",
                name="DeepSeek Coder V2 Lite",
                category=ModelCategory.CODING,
                size_gb=3.5,
                quantization="4-bit",
                context_length=16384,
                description="Efficient coding model with strong Python and JavaScript support",
                performance={"m1": 55, "m2": 75, "m3": 95, "m4": 115},
                features=["code-generation", "fast-inference", "python", "javascript"],
                recommended_for=["web-development", "scripting", "quick-coding"],
                min_memory_gb=6.0,
                popularity_score=8.9
            ),

            # Chat Models
            ModelInfo(
                id="mlx-community/Llama-3.2-8B-Instruct-4bit",
                name="Llama 3.2 8B Instruct",
                category=ModelCategory.CHAT,
                size_gb=4.5,
                quantization="4-bit",
                context_length=8192,
                description="Meta's latest chat model with excellent conversation skills",
                performance={"m1": 40, "m2": 60, "m3": 80, "m4": 95},
                features=["conversation", "safety", "instruction-following"],
                recommended_for=["chatbot", "customer-service", "conversation"],
                min_memory_gb=8.0,
                popularity_score=9.2
            ),
            ModelInfo(
                id="mlx-community/gemma-2-9b-it-4bit",
                name="Gemma 2 9B Instruct",
                category=ModelCategory.CHAT,
                size_gb=5.2,
                quantization="4-bit",
                context_length=8192,
                description="Google's conversational model with strong reasoning",
                performance={"m1": 35, "m2": 50, "m3": 70, "m4": 85},
                features=["reasoning", "conversation", "safety", "multilingual"],
                recommended_for=["complex-conversation", "reasoning", "analysis"],
                min_memory_gb=10.0,
                popularity_score=8.7
            ),

            # Specialized Models
            ModelInfo(
                id="mlx-community/NousHermes-2-Mistral-7B-DPO-4bit",
                name="Nous Hermes 2 Mistral DPO",
                category=ModelCategory.SPECIALIZED,
                size_gb=3.9,
                quantization="4-bit",
                context_length=32768,
                description="Fine-tuned for helpfulness with DPO training",
                performance={"m1": 48, "m2": 68, "m3": 88, "m4": 105},
                features=["helpful", "creative", "storytelling", "roleplay"],
                recommended_for=["creative-writing", "roleplay", "storytelling"],
                min_memory_gb=8.0,
                popularity_score=8.4
            ),
        ]

    def get_all_models(self) -> list[ModelInfo]:
        """Get all available models"""
        return self.models

    def get_models_by_category(self, category: ModelCategory) -> list[ModelInfo]:
        """Get models filtered by category"""
        return [m for m in self.models if m.category == category]

    def get_recommended_models(self,
                             available_memory_gb: float,
                             use_case: str | None = None) -> list[ModelInfo]:
        """Get recommended models based on system capabilities and use case"""
        suitable_models = [
            m for m in self.models
            if m.min_memory_gb <= available_memory_gb
        ]

        if use_case:
            # Filter by recommended use cases
            suitable_models = [
                m for m in suitable_models
                if use_case in m.recommended_for
            ]

        # Sort by popularity score
        suitable_models.sort(key=lambda m: m.popularity_score, reverse=True)

        return suitable_models[:5]  # Return top 5

    def search_models(self, query: str) -> list[ModelInfo]:
        """Search models by name, features, or description"""
        query_lower = query.lower()
        results = []

        for model in self.models:
            # Search in various fields
            if any([
                query_lower in model.name.lower(),
                query_lower in model.description.lower(),
                any(query_lower in f for f in model.features),
                any(query_lower in r for r in model.recommended_for),
                query_lower in model.id.lower()
            ]):
                results.append(model)

        # Sort by relevance (popularity)
        results.sort(key=lambda m: m.popularity_score, reverse=True)

        return results

    def get_model_info(self, model_id: str) -> ModelInfo | None:
        """Get detailed information about a specific model"""
        for model in self.models:
            if model.id == model_id:
                return model
        return None

    def estimate_performance(self, model_id: str, chip_type: str) -> int | None:
        """Estimate tokens/sec for a model on specific hardware"""
        model = self.get_model_info(model_id)
        if not model:
            return None

        # Extract base chip type (m1, m2, m3, m4)
        chip_base = chip_type.lower().split()[0] if chip_type else "m1"

        # Map variations to base types
        chip_mapping = {
            "m1": "m1", "m1 pro": "m1", "m1 max": "m1", "m1 ultra": "m1",
            "m2": "m2", "m2 pro": "m2", "m2 max": "m2", "m2 ultra": "m2",
            "m3": "m3", "m3 pro": "m3", "m3 max": "m3", "m3 ultra": "m3",
            "m4": "m4", "m4 pro": "m4", "m4 max": "m4", "m4 ultra": "m4",
        }

        chip_key = chip_mapping.get(chip_base, "m1")
        base_performance = model.performance.get(chip_key, 50)

        # Adjust for chip variants
        if "ultra" in chip_type.lower():
            return int(base_performance * 1.5)
        elif "max" in chip_type.lower():
            return int(base_performance * 1.3)
        elif "pro" in chip_type.lower():
            return int(base_performance * 1.1)

        return base_performance
