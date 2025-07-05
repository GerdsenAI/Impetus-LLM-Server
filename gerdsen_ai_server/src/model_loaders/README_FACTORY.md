# Model Loader Factory

The Model Loader Factory provides a unified interface for loading various model formats with automatic format detection. It simplifies the process of working with different model types by automatically selecting the appropriate loader based on file content and extension.

## Features

- **Automatic Format Detection**: Detects model format from both file extension and content
- **Unified Interface**: Single entry point for loading any supported model format
- **Format Validation**: Validates model files before loading
- **Loader Caching**: Efficient reuse of loader instances
- **Comprehensive Error Handling**: Clear error messages for common issues
- **Singleton Pattern Support**: Global factory instance for convenience

## Supported Formats

| Format | Extensions | Description |
|--------|------------|-------------|
| GGUF | .gguf | GGML Universal Format - Optimized for CPU/GPU inference |
| SafeTensors | .safetensors | Secure and fast tensor serialization |
| MLX | .mlx | Apple MLX format - Optimized for Apple Silicon |
| CoreML | .mlmodel | Apple CoreML format - iOS/macOS deployment |
| PyTorch | .pth, .pt, .bin | Standard PyTorch model files |
| ONNX | .onnx, .ort | Open Neural Network Exchange - Cross-platform deployment |

## Quick Start

### Basic Usage

```python
from gerdsen_ai_server.src.model_loaders import load_model, detect_format, validate_model

# Load a model with automatic format detection
model = load_model('path/to/model.gguf')

# Detect format without loading
format_type = detect_format('path/to/model.safetensors')
print(f"Detected format: {format_type}")

# Validate a model file
validation = validate_model('path/to/model.onnx')
if validation['valid']:
    print(f"Model is valid {validation['format']} format")
```

### Using the Factory Class

```python
from gerdsen_ai_server.src.model_loaders import ModelLoaderFactory, ModelFormat

# Create factory instance
factory = ModelLoaderFactory()

# Load with format hint (skips detection)
model = factory.load_model(
    'model.bin',
    format_hint=ModelFormat.PYTORCH,
    model_id='my_pytorch_model'
)

# Get all loaded models
loaded_models = factory.get_loaded_models()

# Unload a specific model
factory.unload_model('my_pytorch_model')
```

## Format Detection

The factory uses a two-stage detection process:

1. **Content-based detection**: Checks file headers/magic bytes
2. **Extension-based detection**: Falls back to file extension

Content detection takes precedence when available, ensuring correct format identification even with misleading extensions.

### Detection Examples

```python
# GGUF file with wrong extension - correctly detected as GGUF
format = detect_format('model.txt')  # Contains GGUF magic bytes
# Returns: 'gguf'

# SafeTensors detection via JSON header
format = detect_format('model.safetensors')
# Returns: 'safetensors'

# Directory-based format (MLX)
format = detect_format('path/to/mlx_model/')
# Returns: 'mlx'
```

## Model Validation

Validate models without fully loading them:

```python
result = validate_model('model.gguf')

# Result structure:
{
    'valid': True,
    'format': 'gguf',
    'file_path': 'model.gguf',
    'exists': True,
    'errors': [],
    'warnings': [],
    'metadata': {
        'size_bytes': 4294967296,
        'size_mb': 4096.0,
        'modified': 1234567890.0
    }
}
```

## Advanced Usage

### Custom Loading Parameters

Different loaders accept different parameters:

```python
# PyTorch with device specification
model = load_model(
    'model.pth',
    device='cuda',
    map_location='cuda:0'
)

# SafeTensors with config
model = load_model(
    'model.safetensors',
    model_config={'temperature': 0.7}
)
```

### Direct Loader Access

Access specific loader functionality:

```python
factory = ModelLoaderFactory()

# Get GGUF loader
gguf_loader = factory.create_loader(ModelFormat.GGUF)

# Use loader-specific methods
model_info = gguf_loader.read_metadata('model.gguf')
memory_usage = gguf_loader.estimate_memory_usage('model_id')
```

### Managing Multiple Models

```python
factory = ModelLoaderFactory()

# Load multiple models
models = [
    'llama2.gguf',
    'mistral.safetensors',
    'codegen.pth'
]

for model_path in models:
    try:
        factory.load_model(model_path)
    except Exception as e:
        print(f"Failed to load {model_path}: {e}")

# List all loaded models
all_models = factory.get_loaded_models()
for model_id, info in all_models.items():
    print(f"{model_id}: {info['format']} - {info.get('path', 'N/A')}")

# Clear all models
factory.clear_loaders()
```

## Error Handling

The factory provides clear error messages:

```python
try:
    model = load_model('model.xyz')
except FileNotFoundError:
    print("Model file not found")
except ValueError as e:
    print(f"Format detection failed: {e}")
except RuntimeError as e:
    print(f"Loader error: {e}")
```

## Singleton Pattern

Use the global factory instance for convenience:

```python
from gerdsen_ai_server.src.model_loaders import get_factory

# Get singleton instance
factory = get_factory()

# Same instance everywhere in your application
factory2 = get_factory()
assert factory is factory2
```

## Adding New Formats

To add support for a new format:

1. Create a new loader class in `model_loaders/`
2. Add format to `ModelFormat` enum
3. Update `EXTENSION_MAPPINGS` in factory
4. Add loader class to `LOADER_CLASSES`
5. Optionally add content detection logic

## Performance Considerations

- Loaders are cached and reused
- Content detection reads minimal bytes
- Use format hints to skip detection when format is known
- Clear loaders when done to free memory

## Testing

Run the comprehensive test suite:

```bash
python -m pytest tests/test_model_loader_factory.py -v
```

## Examples

See `examples/model_loader_factory_usage.py` for complete usage examples.