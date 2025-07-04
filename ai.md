# AI Documentation

## Executive Summary
The Impetus-LLM-Server project aims to provide a model-agnostic AI inference platform optimized for Apple Silicon. As of July 2025, the system is in early development with a robust architecture but placeholder functionality. This document outlines the current state, critical issues, architecture, integration with Model Context Protocol (MCP) tools, and a prioritized roadmap for implementation.

- **Status**: Skeleton implementation with critical initialization bug
- **Key Issue**: Import error in `IntegratedMLXManager` (line 106, `gerdsen_ai_server/src/integrated_mlx_manager.py`)
- **Architecture**: Model-agnostic design with Apple Silicon optimization framework
- **Next Steps**: Fix bug, implement model loading, integrate MCP tools

## Quick Navigation
- [Implementation Status](#implementation-status)
- [AI Model Architecture](#ai-model-architecture-model-agnostic-design)
- [Model Configuration](#model-configuration-system)
- [Integration & API](#integration)
- [MCP Integration](#model-context-protocol-mcp-integration)
- [Roadmap & Next Steps](#implementation-roadmap--next-steps)

## Overview
- **Purpose**: To provide a centralized location for AI-related information, models, and configurations used in the project.
- **Scope**: Covers AI model integration, training, inference, optimization strategies for Apple Silicon, and MCP tool integration.

## Implementation Status
- **Current State**: As of July 2025, the AI implementation is in an early stage with placeholder functionality.
  - Model loading and inference logic are placeholders and need actual implementation.
  - API endpoints return simulated responses rather than real model outputs.
- **Known Issues**:
  - Critical bug in `IntegratedMLXManager` initialization: attempting to instantiate non-existent `AppleFrameworksIntegration` instead of `EnhancedAppleFrameworksIntegration` (see line 106 in `gerdsen_ai_server/src/integrated_mlx_manager.py`).
    ```python
    # Incorrect (line 106):
    # self.apple_frameworks = AppleFrameworksIntegration()
    # Correct:
    self.apple_frameworks = EnhancedAppleFrameworksIntegration()
    ```
  - Models are not actually loaded during server startup.
- **Functional Features**:
  - Basic Flask server structure with API endpoints defined.
  - Skeleton for multi-model management through `IntegratedMLXManager`.
  - Apple Silicon detection and optimization framework (partially implemented).
- **Planned Features**:
  - Real model loading and inference for various language models.
  - Performance optimization for Apple Silicon using Core ML, Metal, and Neural Engine.
  - Dynamic model switching based on system state (thermal, power, memory).
  - MCP server integration for external model providers and resources.

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

**Architecture Diagram (ASCII)**:
```
+-------------------+       +-------------------+       +-------------------+
| Flask API Server  | <---> | IntegratedMLXMgr  | <---> | Model Interface   |
+-------------------+       +-------------------+       +-------------------+
                                    |                            |
+-------------------+       +-------------------+       +-------------------+
| MCP Server/Tools  | <---> | Apple Silicon Opt | <---> | Specific Model    |
+-------------------+       +-------------------+       +-------------------+
```

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

## Model Context Protocol (MCP) Integration
The Impetus-LLM-Server supports integration with MCP servers to extend capabilities through external tools and resources. MCP enables connection to model providers, external catalogs, and specialized AI services.

- **MCP Purpose**: Allows the system to access external AI models, configurations, and capabilities without hardcoding specific providers.
- **MCP Components**:
  - **MCP Tools**: Executable functions provided by MCP servers for operations like model discovery, loading, and inference.
    - Example Tool Schema: `get_model_catalog` with parameters `{"provider": "string", "capability": "string"}`
    - Usage: Tools are invoked via the `use_mcp_tool` API with server name and arguments.
  - **MCP Resources**: Data sources like model catalogs or configuration repositories.
    - Example Resource URI: `mcp://model-catalog/huggingface/chat-models`
    - Usage: Resources are accessed via the `access_mcp_resource` API with server name and URI.
- **Integration Points**:
  - **Model Discovery**: MCP tools can populate the `/v1/models` endpoint with external models.
  - **Model Loading**: MCP tools can handle model downloads or remote inference.
  - **Configuration**: MCP resources can provide model configuration files for the system.
  - **API Extension**: MCP tools can add custom endpoints for specialized AI operations.
- **MCP Server Requirements**:
  - Must expose tools following the MCP schema for model operations.
  - Must provide resource URIs for model metadata and configurations.
  - Should support authentication for secure model access (future feature).
- **Example MCP Workflow**:
  ```
  1. Connect to MCP server "huggingface-models"
  2. Use tool "search_models" with {"capability": "chat"} to get model list
  3. Access resource "mcp://huggingface-models/config/model-123" for configuration
  4. Load model using MCP tool "load_remote_model" with configuration
  ```

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

## Implementation Roadmap & Next Steps
The following roadmap prioritizes tasks based on dependencies and impact. Each phase includes success criteria and validation steps.

- **Phase 1: Critical Fixes (Immediate)**
  1. Fix import bug in `integrated_mlx_manager.py` (line 106).
     - **Dependency**: None
     - **Validation**: Server starts without import errors.
     - **Success**: Flask server initializes `IntegratedMLXManager`.
  2. Test server startup with empty model configuration.
     - **Dependency**: Step 1
     - **Validation**: Server responds to `/v1/models` with empty list.
     - **Success**: API endpoints accessible without crashes.

- **Phase 2: Basic Model Loading (Short-Term)**
  1. Implement basic model loading for a single model format (MLX or CoreML).
     - **Dependency**: Phase 1
     - **Validation**: Load a test model and verify with `/api/models/list`.
     - **Success**: Model appears in API response with correct metadata.
  2. Enable placeholder inference returning static responses.
     - **Dependency**: Step 1 of Phase 2
     - **Validation**: Call `/v1/chat/completions` and receive response.
     - **Success**: API returns formatted response without errors.

- **Phase 3: Optimization Features (Medium-Term)**
  1. Implement Apple Silicon detection and device switching.
     - **Dependency**: Phase 2
     - **Validation**: Check logs for device selection based on model size.
     - **Success**: Models load on appropriate device (CPU/GPU/Neural Engine).
  2. Add thermal and power state monitoring with throttling.
     - **Dependency**: Step 1 of Phase 3
     - **Validation**: Simulate high thermal state and verify performance adjustment.
     - **Success**: System reduces performance under thermal stress.

- **Phase 4: MCP Integration & Full Features (Long-Term)**
  1. Connect MCP server for model discovery and configuration.
     - **Dependency**: Phase 2
     - **Validation**: Use `use_mcp_tool` to list external models.
     - **Success**: External models appear in `/v1/models` endpoint.
  2. Implement remote model loading via MCP tools.
     - **Dependency**: Step 1 of Phase 4
     - **Validation**: Load model from MCP resource URI.
     - **Success**: Remote model loads and responds to inference requests.
  3. Add capability-based model selection.
     - **Dependency**: Phase 3
     - **Validation**: Request model by capability instead of ID.
     - **Success**: System selects appropriate model automatically.

- **Success Criteria for MVP**:
  - Server starts without errors.
  - At least one model format loads successfully.
  - Basic inference API endpoints return responses.
  - Apple Silicon optimizations are detected and applied.

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
