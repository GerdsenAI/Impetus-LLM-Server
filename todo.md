# Todo List for Impetus-LLM-Server

This document outlines actionable tasks for the development and maintenance of the Impetus-LLM-Server project, based on the provided README.md documentation. Tasks have been refined with priorities and estimated timelines to align with the project roadmap and guidelines from ai.md.

## Critical Bug Fixes (High Priority)

These tasks address immediate issues preventing proper server initialization and operation.

- [x] **Fix IntegratedMLXManager Import Error** - **Priority: Critical, Timeline: Immediate**
  - Fix line 106 in `gerdsen_ai_server/src/integrated_mlx_manager.py`
  - Change `AppleFrameworksIntegration()` to `EnhancedAppleFrameworksIntegration()`
  - This is preventing the server from starting properly

## VS Code/Cline Integration Requirements (Critical Priority)

These tasks ensure seamless integration with VS Code AI extensions, particularly Cline.

- [ ] **Model Format Support Infrastructure** - **Priority: Critical, Timeline: Immediate**
  - [ ] Create model loader factory pattern to handle all formats dynamically
  - [ ] Implement format-specific loaders inheriting from base loader class
  - [ ] Add model format validation and compatibility checking
  - [ ] Create unified inference interface regardless of underlying format

- [ ] **Model Management UI** - **Priority: Critical, Timeline: Sprint 1**
  - [ ] Design React component for model selection and management
  - [ ] Implement drag-and-drop model upload functionality
  - [ ] Add Hugging Face model search and download interface
  - [ ] Create model library view with filtering by format, size, and capability
  - [ ] Add real-time download progress and model conversion status

- [ ] **OpenAI API Enhancement for Model Switching** - **Priority: Critical, Timeline: Sprint 1**
  - [ ] Extend `/v1/models` endpoint to return all loaded models with metadata
  - [ ] Add model parameter validation in chat/completion endpoints
  - [ ] Implement dynamic model switching without server restart
  - [ ] Add model-specific configuration (context length, tokens/sec, etc.)
  - [ ] Ensure proper error handling for unsupported model requests

## Development Tasks

These tasks focus on implementing upcoming features as outlined in the project's roadmap. Priorities and timelines are set to focus on immediate needs first.

- [x] **Multi-Model Support (Initial Setup)**: Basic structure for loading and running multiple models simultaneously has been implemented in `src/models/multi_model_manager.py`.
- [x] **Model Configuration System**: Models are now loaded from configuration files in the `config/models` directory.
- [x] **Database Integration**: The server is now connected to a SQLite database for model management.
- [ ] **Multi-Model Support (Integration)** - **Priority: High, Timeline: Next 1-2 Sprints**
  - [ ] Review existing structure in `src/models/multi_model_manager.py` for current implementation.
  - [ ] Integrate AI models like Llama and Mistral into `MultiModelManager` for seamless operation.
  - [ ] Ensure compatibility with Apple Silicon optimization practices.
- [ ] **Multi-Model Support (API Endpoints)** - **Priority: High, Timeline: Next 1-2 Sprints**
  - [ ] Develop FastAPI endpoints in `src/main.py` for dynamic model interaction.
  - [ ] Implement endpoints for model selection and switching under `/v1/chat/completions` and `/v1/models`.
  - [ ] Apply CORS and rate-limiting configurations for security.
- [ ] **Universal Local Model Support for VS Code/Cline Integration** - **Priority: Critical, Timeline: Immediate**
  - [ ] Implement dynamic model format detection and loading system:
    - [ ] GGUF format support (.gguf files) - Most common for quantized models
    - [ ] SafeTensors support (.safetensors) - Hugging Face standard format
    - [ ] MLX native format (.mlx, .npz) - Apple Silicon optimized
    - [ ] CoreML models (.mlmodel, .mlpackage) - iOS/macOS native
    - [ ] Foundation models - Direct Apple framework integration
    - [ ] PyTorch formats (.pt, .pth, .bin) - Standard deep learning format
    - [ ] ONNX format (.onnx) - Cross-platform compatibility
  - [ ] Create unified model management interface:
    - [ ] Model browser UI with format filtering
    - [ ] Download manager for Hugging Face models with progress tracking
    - [ ] Local file browser option for selecting models from disk
    - [ ] URL/link input for direct model downloads
    - [ ] Automatic format conversion when needed (e.g., PyTorch to MLX)
  - [ ] Implement model discovery and cataloging:
    - [ ] Auto-scan common model directories
    - [ ] Hugging Face model hub integration with search
    - [ ] Model metadata extraction (size, quantization, capabilities)
    - [ ] Model compatibility checking for VS Code extensions
  - [ ] VS Code/Cline specific optimizations:
    - [ ] Ensure streaming support for all model formats
    - [ ] Implement proper tokenization for each model type
    - [ ] Add model-specific prompt templates
    - [ ] Test with Cline, Continue.dev, and other popular extensions
  - [ ] Create model switching API endpoint for dynamic selection
  - [ ] Initialize models on server startup with Apple Silicon optimization
- [ ] **API Response Implementation** - **Priority: High, Timeline: Next Sprint**
  - [ ] Replace placeholder responses in `/v1/chat/completions` with actual model outputs.
  - [ ] Implement real text generation capabilities in `/v1/completions`.
  - [ ] Add proper embedding generation in `/v1/embeddings`.
  - [ ] Connect API endpoints to model predictions for meaningful responses.
- [ ] **Custom Model Training** - **Priority: Medium, Timeline: Next 3-4 Sprints**
  - [ ] Design framework for fine-tuning models on local data using Core ML and MLX.
  - [ ] Create API endpoint or interface for initiating and monitoring training.
- [ ] **Advanced Scheduling** - **Priority: Medium, Timeline: Next 3-4 Sprints**
  - [ ] Implement time-based optimization and task scheduling.
  - [ ] Integrate with macOS service for background operations, focusing on thermal and power efficiency.
- [ ] **Cloud Integration** - **Priority: Low, Timeline: Later Sprints**
  - [ ] Develop optional cloud model synchronization with security and privacy features.
  - [ ] Add configuration options in `config/production.json` for cloud features.
- [ ] **Plugin System** - **Priority: Low, Timeline: Later Sprints**
  - [ ] Design extensible architecture for third-party integrations.
  - [ ] Document plugin system for community contributions.

## Testing and Validation

These tasks ensure the stability and functionality of the server after critical fixes and implementations.

- [ ] **Server Initialization Testing** - **Priority: Critical, Timeline: Immediate**
  - [x] Verify server starts without errors after bug fixes.
  - [x] Confirm all models load successfully during initialization.
  - [x] Test each API endpoint to ensure they return meaningful responses.
  - [ ] Validate Apple Silicon optimizations are applied correctly.

## Documentation Tasks

These tasks aim to enhance the project's documentation for better user and developer experience. They will be handled concurrently with development tasks.

- [ ] **Expand User Guides** - **Priority: High, Timeline: Ongoing with Development Milestones**
  - [ ] Create guides for new features like multi-model support and custom training.
  - [ ] Use Markdown format in `docs/` directory for consistency.
- [ ] **Technical Documentation** - **Priority: High, Timeline: Ongoing with Development**
  - [ ] Document architecture changes for multi-model support and API endpoints in `docs/enhanced_architecture_design.md`.
  - [ ] Detail new API endpoints in `docs/API_REFERENCE.md`.
- [ ] **Update Troubleshooting Section** - **Priority: Medium, Timeline: Post-Feature Implementation**
  - [ ] Add solutions for common issues with new features in relevant documentation.

## Community and Contribution Tasks

These tasks encourage community involvement and streamline contribution processes, planned for later stages after core functionality.

- [ ] **Contribution Guidelines** - **Priority: Low, Timeline: After Major Development Tasks**
  - [ ] Draft guidelines for contributing, including coding standards and pull request processes in `docs/`.
- [ ] **Review Pull Requests** - **Priority: Low, Timeline: Ongoing as Submitted**
  - [ ] Set up process for reviewing community contributions for alignment with project goals.
- [ ] **Community Engagement** - **Priority: Low, Timeline: Post-Major Development**
  - [ ] Propose forums or channels for user and developer discussions.

---

**Note**: This todo list is a living document and should be updated as tasks are completed or new priorities emerge. Timelines and priorities are based on the current project roadmap and may be adjusted based on feedback or changing requirements.
