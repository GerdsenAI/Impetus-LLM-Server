# ONNX Model Loader

The ONNX (Open Neural Network Exchange) model loader provides cross-platform support for loading and running ONNX models with optimizations for various hardware accelerators, including Apple Silicon.

## Features

- **Cross-Platform Support**: Works on macOS, Windows, and Linux
- **Apple Silicon Optimization**: Automatic detection and use of CoreML execution provider on Apple devices
- **Multiple Execution Providers**: Supports CPU, CUDA, DirectML, CoreML, and more
- **Model Architecture Detection**: Automatically identifies CNN, RNN, Transformer, and other architectures
- **Metadata Extraction**: Extracts producer info, custom metadata, and model descriptions
- **Model Validation**: Built-in ONNX model validation
- **Memory Estimation**: Calculates estimated memory usage
- **Device-Specific Optimization**: Optimizes model execution based on available hardware

## Installation

```bash
# Basic installation
pip install onnx onnxruntime

# For Apple Silicon with CoreML support
pip install onnxruntime-silicon

# For NVIDIA GPU support
pip install onnxruntime-gpu
```

## Usage

### Basic Model Loading

```python
from gerdsen_ai_server.src.model_loaders.onnx_loader import ONNXLoader

# Initialize loader
loader = ONNXLoader()

# Check if file is supported
if loader.can_load("model.onnx"):
    # Load the model
    model_info = loader.load_model("model.onnx")
    
    # Access model information
    print(f"Architecture: {model_info['architecture']}")
    print(f"Parameters: {model_info['total_parameters']:,}")
    print(f"Providers: {model_info['providers']}")
```

### Running Inference

```python
import numpy as np

# Prepare input data (adjust shape based on your model)
input_data = {
    'input': np.random.randn(1, 3, 224, 224).astype(np.float32)
}

# Run inference
model_id = "my_model"  # Model ID from loading
outputs = loader.run_inference(model_id, input_data)

# Process outputs
for name, output in outputs.items():
    print(f"{name}: {output.shape}")
```

### Apple Silicon Optimization

```python
# Define device profile for Apple Silicon
device_profile = {
    'platform': 'darwin',
    'has_neural_engine': True,
    'neural_engine_cores': 16,
    'has_gpu': True,
    'gpu_vendor': 'apple'
}

# Optimize model for device
loader.optimize_for_device(model_id, device_profile)
```

### Model Management

```python
# List loaded models
models = loader.list_loaded_models()

# Get model information
info = loader.get_model_info(model_id)

# Unload model
loader.unload_model(model_id)
```

## Supported Architectures

The loader automatically detects the following architectures:

- **CNN**: Convolutional Neural Networks (detected by Conv/ConvTranspose ops)
- **RNN**: Recurrent Neural Networks (LSTM, GRU, RNN ops)
- **Transformer**: Attention-based models (Attention/MultiHeadAttention ops)
- **Hybrid**: Combined architectures (e.g., CNN+RNN)
- **Feedforward**: Simple dense networks

## Execution Providers

The loader automatically selects the best available execution providers:

1. **CoreMLExecutionProvider**: For Apple Silicon devices with Neural Engine
2. **CUDAExecutionProvider**: For NVIDIA GPUs
3. **DmlExecutionProvider**: For DirectML on Windows
4. **CPUExecutionProvider**: Universal fallback

## Model Information

The loader extracts comprehensive model information:

```python
{
    'format': 'onnx',
    'architecture': 'cnn',
    'total_parameters': 25557032,
    'estimated_memory_mb': 97.5,
    'providers': ['CoreMLExecutionProvider', 'CPUExecutionProvider'],
    'input_info': [
        {'name': 'input', 'shape': [1, 3, 224, 224], 'type': 'tensor(float)'}
    ],
    'output_info': [
        {'name': 'output', 'shape': [1, 1000], 'type': 'tensor(float)'}
    ],
    'metadata': {
        'producer': 'pytorch',
        'custom': {...}
    }
}
```

## Testing

Run the comprehensive test suite:

```bash
pytest tests/model_loaders/test_onnx_loader.py -v
```

## Performance Tips

1. **Use Hardware Acceleration**: Install appropriate ONNX Runtime packages for your hardware
2. **Optimize for Device**: Call `optimize_for_device()` with your hardware profile
3. **Batch Processing**: Process multiple inputs together when possible
4. **Model Quantization**: Use quantized models for faster inference
5. **Provider Selection**: Manually specify providers for fine-grained control

## Troubleshooting

### CoreML Provider Not Available
- Ensure you're on macOS with Apple Silicon
- Install `onnxruntime-silicon` instead of regular `onnxruntime`

### Model Validation Fails
- Check ONNX model version compatibility
- Verify model was exported correctly
- Use `loader.validate_model()` for detailed error messages

### Memory Issues
- Check `estimated_memory_mb` before loading large models
- Unload models when not in use
- Consider model quantization or pruning