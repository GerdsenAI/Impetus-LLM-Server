#!/usr/bin/env python3
"""
Import helper for bundled environment
Provides compatibility layer between development and bundled imports
"""

import sys
import importlib
import logging

logger = logging.getLogger(__name__)

class BundledImportHelper:
    """Helper class to handle import differences in bundled environment"""
    
    @staticmethod
    def import_module(module_path, fallback_names=None):
        """
        Try to import a module with multiple strategies
        
        Args:
            module_path: Full module path (e.g., 'gerdsen_ai_server.src.module')
            fallback_names: List of alternative module names to try
        
        Returns:
            Imported module or None
        """
        # Strategy 1: Try the full path (works in development)
        try:
            return importlib.import_module(module_path)
        except ImportError:
            pass
        
        # Strategy 2: Try without the package prefix (works in bundled)
        if module_path.startswith('gerdsen_ai_server.src.'):
            simple_name = module_path.replace('gerdsen_ai_server.src.', '')
            try:
                return importlib.import_module(simple_name)
            except ImportError:
                pass
        
        # Strategy 3: Try fallback names
        if fallback_names:
            for name in fallback_names:
                try:
                    return importlib.import_module(name)
                except ImportError:
                    pass
        
        logger.warning(f"Failed to import module: {module_path}")
        return None
    
    @staticmethod
    def get_class(module, class_name):
        """Get a class from a module safely"""
        if module and hasattr(module, class_name):
            return getattr(module, class_name)
        return None

# Create bundled-compatible imports
def setup_bundled_imports():
    """Setup import mappings for bundled environment"""
    helper = BundledImportHelper()
    
    # Import all required modules
    modules = {
        'enhanced_apple_frameworks_integration': helper.import_module(
            'gerdsen_ai_server.src.enhanced_apple_frameworks_integration',
            ['enhanced_apple_frameworks_integration']
        ),
        'enhanced_apple_silicon_detector': helper.import_module(
            'gerdsen_ai_server.src.enhanced_apple_silicon_detector',
            ['enhanced_apple_silicon_detector']
        ),
        'dummy_model_loader': helper.import_module(
            'gerdsen_ai_server.src.dummy_model_loader',
            ['dummy_model_loader']
        ),
        'model_loaders': helper.import_module(
            'gerdsen_ai_server.src.model_loaders',
            ['model_loaders']
        ),
        'inference': helper.import_module(
            'gerdsen_ai_server.src.inference',
            ['inference']
        ),
        'model_paths': helper.import_module(
            'gerdsen_ai_server.src.config.model_paths',
            ['config.model_paths', 'model_paths']
        ),
    }
    
    # Extract classes and functions
    classes = {}
    
    if modules['enhanced_apple_frameworks_integration']:
        classes['EnhancedAppleFrameworksIntegration'] = helper.get_class(
            modules['enhanced_apple_frameworks_integration'],
            'EnhancedAppleFrameworksIntegration'
        )
    
    if modules['enhanced_apple_silicon_detector']:
        classes['EnhancedAppleSiliconDetector'] = helper.get_class(
            modules['enhanced_apple_silicon_detector'],
            'EnhancedAppleSiliconDetector'
        )
    
    if modules['dummy_model_loader']:
        classes['load_dummy_model'] = getattr(modules['dummy_model_loader'], 'load_dummy_model', None)
        classes['dummy_predict'] = getattr(modules['dummy_model_loader'], 'dummy_predict', None)
    
    if modules['model_loaders']:
        for loader in ['GGUFLoader', 'SafeTensorsLoader', 'MLXLoader', 
                      'CoreMLLoader', 'PyTorchLoader', 'ONNXLoader', 
                      'ModelLoaderFactory']:
            classes[loader] = helper.get_class(modules['model_loaders'], loader)
        classes['LoaderModelFormat'] = helper.get_class(modules['model_loaders'], 'ModelFormat')
    
    if modules['inference']:
        for cls in ['GGUFInferenceEngine', 'GenerationConfig', 
                   'UnifiedInferenceEngine', 'get_unified_inference_engine']:
            if cls == 'get_unified_inference_engine':
                classes[cls] = getattr(modules['inference'], cls, None)
            else:
                classes[cls] = helper.get_class(modules['inference'], cls)
    
    if modules['model_paths']:
        classes['get_model_paths'] = getattr(modules['model_paths'], 'get_model_paths', None)
        classes['get_model_search_paths'] = getattr(modules['model_paths'], 'get_model_search_paths', None)
    
    return modules, classes