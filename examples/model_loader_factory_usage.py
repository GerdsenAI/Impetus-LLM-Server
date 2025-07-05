"""
Example usage of the Model Loader Factory

This script demonstrates how to use the model loader factory to:
1. Detect model formats
2. Validate model files
3. Load models with automatic format detection
4. Manage loaded models
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gerdsen_ai_server.src.model_loaders import (
    ModelLoaderFactory,
    ModelFormat,
    get_factory,
    load_model,
    detect_format,
    validate_model
)


def main():
    """Demonstrate model loader factory usage"""
    
    print("=== Model Loader Factory Usage Examples ===\n")
    
    # Example 1: Using the factory directly
    print("1. Creating a factory instance:")
    factory = ModelLoaderFactory()
    
    # Show supported formats
    print("\nSupported formats:")
    formats = factory.get_supported_formats()
    for format_name, info in formats.items():
        print(f"  - {format_name}: {info['description']}")
        print(f"    Extensions: {', '.join(info['extensions'])}")
    
    # Example 2: Format detection
    print("\n\n2. Format Detection Examples:")
    
    # Simulate different file paths
    test_files = [
        "model.gguf",
        "model.safetensors",
        "model.pth",
        "model.onnx",
        "model.mlmodel",
        "model.bin",
        "unknown.xyz"
    ]
    
    for filename in test_files:
        # For demonstration, we'll just show extension-based detection
        file_path = Path(filename)
        try:
            # Using convenience function
            detected = detect_format(file_path)
            print(f"  {filename} -> {detected}")
        except Exception as e:
            print(f"  {filename} -> Error: {e}")
    
    # Example 3: Model validation
    print("\n\n3. Model Validation Example:")
    
    # For demonstration, create a dummy validation
    print("  Validating a model file (simulated):")
    validation_result = {
        'valid': True,
        'format': 'gguf',
        'file_path': '/path/to/model.gguf',
        'exists': True,
        'errors': [],
        'warnings': [],
        'metadata': {
            'size_mb': 4096.5,
            'size_bytes': 4294967296
        }
    }
    
    print(f"  Valid: {validation_result['valid']}")
    print(f"  Format: {validation_result['format']}")
    print(f"  Size: {validation_result['metadata']['size_mb']:.1f} MB")
    if validation_result['errors']:
        print(f"  Errors: {', '.join(validation_result['errors'])}")
    if validation_result['warnings']:
        print(f"  Warnings: {', '.join(validation_result['warnings'])}")
    
    # Example 4: Loading models
    print("\n\n4. Loading Models Example:")
    
    print("\n  a) Load with automatic format detection:")
    print("     result = load_model('model.gguf')")
    print("     # Automatically detects GGUF format and uses appropriate loader")
    
    print("\n  b) Load with format hint:")
    print("     result = factory.load_model('model.bin', format_hint=ModelFormat.PYTORCH)")
    print("     # Skips detection and uses PyTorch loader directly")
    
    print("\n  c) Load with custom parameters:")
    print("     result = factory.load_model('model.safetensors', ")
    print("                                model_id='my_model',")
    print("                                model_config={'device': 'cuda'})")
    
    # Example 5: Managing loaded models
    print("\n\n5. Managing Loaded Models:")
    
    print("\n  Get all loaded models:")
    print("     models = factory.get_loaded_models()")
    print("     # Returns dict of all models across all loaders")
    
    print("\n  Unload a specific model:")
    print("     success = factory.unload_model('model_id')")
    print("     # Searches all loaders and unloads the model")
    
    print("\n  Clear all loaders:")
    print("     factory.clear_loaders()")
    print("     # Unloads all models and clears loader instances")
    
    # Example 6: Using singleton pattern
    print("\n\n6. Using Singleton Factory:")
    
    print("  The factory can be used as a singleton:")
    print("     factory = get_factory()  # Gets or creates singleton instance")
    print("     # All convenience functions use this singleton")
    
    # Example 7: Error handling
    print("\n\n7. Error Handling:")
    
    print("\n  FileNotFoundError: When model file doesn't exist")
    print("  ValueError: When model format cannot be detected")
    print("  RuntimeError: When no loader is available for the format")
    
    # Example 8: Advanced usage
    print("\n\n8. Advanced Usage:")
    
    print("\n  Custom format detection:")
    print("     # Check file content first, then extension")
    print("     format_type = factory.detect_format_from_file('model.dat')")
    print("     # May detect GGUF even if extension is .dat")
    
    print("\n  Direct loader access:")
    print("     # Get specific loader instance")
    print("     gguf_loader = factory.create_loader(ModelFormat.GGUF)")
    print("     # Use loader-specific methods")
    print("     model_info = gguf_loader.read_metadata('model.gguf')")
    
    print("\n\n=== End of Examples ===")


def demonstrate_real_usage():
    """Demonstrate with actual file operations (if models exist)"""
    
    print("\n\n=== Real Usage Demo ===")
    
    # Get factory instance
    factory = get_factory()
    
    # Example model paths (adjust to your environment)
    example_models = [
        "/path/to/llama-2-7b.gguf",
        "/path/to/model.safetensors",
        "/path/to/model.pth"
    ]
    
    for model_path in example_models:
        if Path(model_path).exists():
            print(f"\nProcessing: {model_path}")
            
            try:
                # Detect format
                format_type = factory.detect_format_from_file(model_path)
                print(f"  Detected format: {format_type.value}")
                
                # Validate
                validation = factory.validate_model_file(model_path)
                print(f"  Valid: {validation['valid']}")
                print(f"  Size: {validation['metadata'].get('size_mb', 0):.1f} MB")
                
                # Load model
                model_data = factory.load_model(model_path)
                print(f"  Loaded successfully!")
                print(f"  Model ID: {model_data.get('id', 'N/A')}")
                
                # Get loaded models
                loaded = factory.get_loaded_models()
                print(f"  Total loaded models: {len(loaded)}")
                
            except Exception as e:
                print(f"  Error: {e}")
    
    # Clean up
    factory.clear_loaders()
    print("\nAll models unloaded and loaders cleared.")


if __name__ == "__main__":
    main()
    
    # Uncomment to run real usage demo
    # demonstrate_real_usage()