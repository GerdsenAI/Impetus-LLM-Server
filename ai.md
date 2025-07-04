# AI Documentation

This file contains documentation and notes related to the AI components of the Impetus-LLM-Server project.

## Overview
- **Purpose**: To provide a centralized location for AI-related information, models, and configurations used in the project.
- **Scope**: Covers AI model integration, training, inference, and optimization strategies for Apple Silicon environments.

## Implementation Status
- **Current State**: As of July 2025, the AI implementation is in an early stage with placeholder functionality.
  - Model loading and inference logic are placeholders and need actual implementation.
  - API endpoints return simulated responses rather than real model outputs.
- **Known Issues**:
  - Critical bug in `IntegratedMLXManager` initialization: attempting to instantiate non-existent `AppleFrameworksIntegration` instead of `EnhancedAppleFrameworksIntegration` (see line 106 in `gerdsen_ai_server/src/integrated_mlx_manager.py`).
  - Models are not actually loaded during server startup.
- **Functional Features**:
  - Basic Flask server structure with API endpoints defined.
  - Skeleton for multi-model management through `IntegratedMLXManager`.
  - Apple Silicon detection and optimization framework (partially implemented).
- **Planned Features**:
  - Real model loading and inference for various language models.
  - Performance optimization for Apple Silicon using Core ML, Metal, and Neural Engine.
  - Dynamic model switching based on system state (thermal, power, memory).

## AI Model Architecture (Model-Agnostic Design)
The Impetus-LLM-Server is designed to be model-agnostic, supporting any language model or AI framework through a generic interface and configuration system. Specific models are not hardcoded into the system but are instead defined through configuration.

- **Generic Model Interface**:
  - **Purpose**: Defines a standard contract that any AI model must implement to be used within the system.
  - **Key Methods**:
    - `load()`: Loads the model into memory with given configuration.
    - `predict()`: Generates predictions based on input data and parameters.
    - `unload()`: Frees memory and resources when the model is no longer needed.
    - `get_metadata()`: Returns model capabilities, limitations, and requirements.
  - **Benefits**: Allows for plug-and-play model integration without modifying core server code.
- **Model Categories and Capabilities**:
  - Models are categorized by capability rather than specific implementation:
    - **Chat Models**: Designed for conversational interactions.
    - **Completion Models**: Focused on text generation from prompts.
    - **Embedding Models**: Generate vector representations of text.
    - **Multimodal Models**: Handle text, image, or other data types (future support planned).
  - Capability flags define what operations a model supports, allowing dynamic selection based on task requirements.

## Model Configuration System
Models are defined through configuration rather than hardcoding, enabling flexibility and extensibility.

- **Configuration Format**: Models are specified in JSON/YAML configuration files or through API uploads with the following properties:
  - `model_id`: Unique identifier for the model (e.g., "model-001").
  - `display_name`: Human-readable name for the model.
  - `model_type`: Category of model (chat, completion, embedding, etc.).
  - `path`: Local file path or download URL for model weights.
  - `framework`: Underlying framework (MLX, CoreML, ONNX, etc.).
  - `capabilities`: List of supported operations (e.g., ["chat", "completion"]).
  - `requirements`: Hardware requirements (e.g., {"memory_gb": 8, "compute": "gpu"}).
  - `optimization_hints`: Preferred optimization strategies (e.g., {"device": "neural_engine", "quantization": "int8"}).
- **Configuration Location**: Model configurations are stored in a designated directory (planned: `config/models/`) or database.
- **Dynamic Loading**:
  - Models are loaded at server startup based on configuration.
  - Supports hot-loading of new models without server restart.
  - Auto-discovery of model configuration files in designated directories.
  - Plugin-based architecture for supporting different model formats and frameworks.

## Integration
- **Integration Architecture**:
  - **Core Component**: `IntegratedMLXManager` serves as the central AI model manager, instantiated in `app.py` during Flask server startup.
  - **Framework Layers**:
    - **Apple Frameworks**: Utilizes `EnhancedAppleFrameworksIntegration` for Core ML, Metal, and Neural Engine integration.
    - **Model Managers**: Separate managers for Core ML (`EnhancedCoreMLManager`) and MLX (`EnhancedMLXManager`) models, with extensibility for other frameworks.
    - **Hardware Optimization**: Dynamic adjustment of compute device (CPU/GPU/Neural Engine) based on system state via `EnhancedAppleSiliconDetector`.
  - **Relationship with Flask App**:
    - Flask app in `app.py` initializes `IntegratedMLXManager` as a global `ai_manager`.
    - API endpoints call `ai_manager` methods for model listing, predictions, and management.
    - Responses are formatted to match OpenAI API structure for compatibility.
- **Initialization Procedure**:
  - **Server Startup**: Flask app creates `IntegratedMLXManager` instance, which loads models based on configuration (currently placeholder).
  - **Model Loading**: Models are loaded from a cache directory (`~/.gerdsen_ai/model_cache`) or downloaded if not present (not yet implemented).
  - **Optimization**: Apple Silicon optimizations are applied based on detected hardware capabilities and model-specific hints (partially implemented).
  - **Monitoring**: System state monitoring for thermal, power, and memory conditions is initialized (skeleton only).
- **API Endpoints**:
  - `/v1/models`: Lists all available models with metadata like capabilities and requirements.
  - `/v1/chat/completions`: Creates chat completions using the specified model; currently returns placeholder responses.
  - `/v1/completions`: Generates text completions for given prompts; needs actual text generation.
  - `/v1/embeddings`: Produces embeddings using the specified model; needs real vector output.
  - `/api/models/upload`: Allows uploading new models and configurations (placeholder implementation).
  - `/api/models/list`: Lists all loaded models with detailed status.
  - `/api/models/optimize`: Optimizes an existing model for performance based on hints (placeholder).

## API Rules and Workflows
- **Model Selection and Switching**:
  - **Default Behavior**: If no model is specified in a request, a default model (configured in system settings) is used.
  - **Explicit Selection**: Requests can specify a model ID from the `/v1/models` list.
  - **Capability-Based Selection**: Future feature to select models by capability (e.g., "any chat model") rather than specific ID.
  - **Dynamic Switching**: System may switch models or compute devices based on thermal state, power conditions, or memory pressure (planned feature).
- **Request/Response Formats**:
  - **Chat Completions (`/v1/chat/completions`)**:
    - **Request**: JSON with `model` (optional), `messages` array (role/content pairs).
    - **Response**: OpenAI-compatible format with `choices` array containing assistant message content.
    - **Example**:
      ```
      POST /v1/chat/completions
      {
        "model": "model-001",
        "messages": [{"role": "user", "content": "Hello"}]
      }
      Response:
      {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1625097600,
        "model": "model-001",
        "choices": [{"message": {"role": "assistant", "content": "Hello! How can I help?"}, "finish_reason": "stop", "index": 0}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
      }
      ```
  - **Text Completions (`/v1/completions`)**:
    - **Request**: JSON with `model` (optional), `prompt` string.
    - **Response**: OpenAI-compatible format with `choices` array containing generated text.
  - **Embeddings (`/v1/embeddings`)**:
    - **Request**: JSON with `model` (optional), `input` text.
    - **Response**: OpenAI-compatible format with `data` array containing embedding vectors.
- **Rate Limiting and Security**:
  - **Rate Limits**: To be implemented; planned limits of 100 requests/minute per client (adjustable).
  - **Authentication**: Currently none; planned API key system for production use.
  - **CORS**: Enabled for all origins (needs restriction in production).
- **Error Handling**:
  - **Model Not Found**: Returns 404 with JSON error message if specified model doesn't exist.
  - **Prediction Failure**: Returns 500 with JSON error if inference fails.
  - **Invalid Input**: Returns 400 with JSON error for malformed requests.

## Development Workflows
- **Model Loading and Unloading**:
  - **Loading**: Use `/api/models/upload` endpoint or direct file path loading via `ai_manager.load_model()`; specify model configuration or path.
  - **Unloading**: Call `ai_manager.unload_model(model_id)` to free memory for unused models (needs full implementation).
  - **Cache Management**: Models are cached in `~/.gerdsen_ai/model_cache`; old versions should be cleared automatically (planned).
- **Adding New Models**:
  - **Configuration**: Create a new model configuration file or upload through API with necessary properties.
  - **Framework Support**: Ensure the model framework is supported or extend the system with a new adapter.
  - **Testing**: Verify model capabilities through API endpoints or internal testing tools (planned).
- **Performance Monitoring**:
  - **Metrics Collection**: System collects inference time, memory usage, and throughput (skeleton only).
  - **API Access**: Performance data available via `/api/system/info` endpoint.
  - **Optimization Triggers**: Automatic optimization based on high CPU/memory usage or thermal state (planned).
- **Debugging and Troubleshooting**:
  - **Logs**: Check Flask server logs for initialization errors; model-specific logs in manager classes.
  - **Common Issues**:
    - Import error in `IntegratedMLXManager` (see known issues).
    - Model loading failures due to missing files or incompatible formats.
  - **Debug Mode**: Set `DEBUG=true` environment variable for detailed logging in Flask.

## Configuration Management
- **Environment Variables**:
  - `PORT`: Server port (default 5000).
  - `DEBUG`: Enable debug logging (default False).
  - `MODEL_CONFIG_DIR`: Directory for model configuration files (planned).
- **Configuration Files**:
  - Currently none; planned `config/production.json` for system settings and `config/models/` directory for model definitions.
- **Model Path Configuration**:
  - Default cache directory: `~/.gerdsen_ai/model_cache`.
  - Custom paths can be specified in model configurations.
- **Runtime Optimization Settings**:
  - `auto_optimization`: Boolean to enable/disable automatic Apple Silicon optimizations (default True).
  - `thermal_throttling`: Boolean to enable thermal management adjustments (default True).
  - `power_management`: Boolean to enable power efficiency adjustments (default True).

## Future Enhancements
- **Planned Improvements**:
  - Implement actual model loading and inference logic beyond placeholders.
  - Enhance optimization techniques for Apple Silicon, including quantization and dynamic batch sizing.
  - Expand support for additional model formats and frameworks through plugin architecture.
  - Develop a more robust model upload and management system through the API.
  - Integrate performance monitoring and metrics collection for real-time model evaluation.
  - Add authentication and rate limiting for production security.
  - Implement cloud synchronization for model updates (optional feature).
  - Capability-based model selection for automatic matching of models to tasks.

## Notes
- This document will be updated as implementation progresses.
- Additional documentation for specific workflows (like model training) may be created as separate files in the `docs/` directory.
- Any research findings related to Apple Silicon optimization will be added here or in `research_findings.md`.
