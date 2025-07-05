"""
Example usage of the ONNX model loader
"""

import numpy as np
from gerdsen_ai_server.src.model_loaders.onnx_loader import ONNXLoader


def main():
    # Initialize the ONNX loader
    loader = ONNXLoader()
    
    # Check device capabilities
    print("ONNX Runtime Device Info:")
    device_info = loader.get_device_info()
    for key, value in device_info.items():
        print(f"  {key}: {value}")
    print()
    
    # Example 1: Load an ONNX model
    model_path = "path/to/your/model.onnx"
    
    # Check if the loader can handle this file
    if loader.can_load(model_path):
        print(f"Loading model from: {model_path}")
        
        try:
            # Load the model
            model_info = loader.load_model(model_path)
            
            # Display model information
            print("\nModel Information:")
            print(f"  Format: {model_info['format']}")
            print(f"  Architecture: {model_info['architecture']}")
            print(f"  Total Parameters: {model_info['total_parameters']:,}")
            print(f"  Memory Usage: {model_info['estimated_memory_mb']:.2f} MB")
            print(f"  Optimized for: {model_info['optimized_for']}")
            print(f"  Providers: {model_info['providers']}")
            
            # Display input/output info
            print("\nInputs:")
            for inp in model_info['input_info']:
                print(f"  - {inp['name']}: shape={inp['shape']}, type={inp['type']}")
                
            print("\nOutputs:")
            for out in model_info['output_info']:
                print(f"  - {out['name']}: shape={out['shape']}, type={out['type']}")
                
            # Example 2: Optimize for Apple Silicon (if available)
            if 'CoreMLExecutionProvider' in device_info.get('providers', []):
                print("\nOptimizing for Apple Silicon...")
                device_profile = {
                    'platform': 'darwin',
                    'has_neural_engine': True,
                    'neural_engine_cores': 16,
                    'has_gpu': True,
                    'gpu_vendor': 'apple'
                }
                
                model_id = "my_model"  # Use the stem of the filename
                if loader.optimize_for_device(model_id, device_profile):
                    print("Successfully optimized for Apple Silicon!")
                    
            # Example 3: Run inference
            print("\nRunning inference...")
            
            # Prepare input (example for image model)
            # Adjust the shape based on your model's requirements
            batch_size = 1
            channels = 3
            height = 224
            width = 224
            
            input_data = {
                'input': np.random.randn(batch_size, channels, height, width).astype(np.float32)
            }
            
            # Run inference
            outputs = loader.run_inference(model_id, input_data)
            
            print("Inference Results:")
            for name, output in outputs.items():
                print(f"  {name}: shape={output.shape}, dtype={output.dtype}")
                
            # Example 4: Model management
            print("\nLoaded models:", loader.list_loaded_models())
            
            # Unload the model when done
            if loader.unload_model(model_id):
                print(f"Successfully unloaded model: {model_id}")
                
        except Exception as e:
            print(f"Error: {e}")
            
    else:
        print(f"File {model_path} is not in ONNX format")
        
    # Example 5: Validate a model file
    print("\nValidating ONNX model...")
    is_valid, error = loader.validate_model(model_path)
    if is_valid:
        print("Model is valid!")
    else:
        print(f"Model validation failed: {error}")


if __name__ == "__main__":
    main()