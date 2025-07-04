#!/usr/bin/env python3
"""
Service Management API Routes
Provides API endpoints for managing macOS service functionality
"""

from flask import Blueprint, jsonify, request
import logging
import sys
import os
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

service_mgmt_bp = Blueprint('service_management', __name__)
logger = logging.getLogger(__name__)

# Global service manager instance
_service_manager = None

def get_service_manager():
    """Get or create service manager instance"""
    global _service_manager
    if _service_manager is None:
        try:
            from src.macos_service_integration import MacOSServiceManager
            _service_manager = MacOSServiceManager()
        except ImportError as e:
            logger.error(f"Service integration not available: {e}")
            return None
    return _service_manager

@service_mgmt_bp.route('/status', methods=['GET'])
def get_service_status():
    """Get current service status"""
    try:
        service_manager = get_service_manager()
        if not service_manager:
            return jsonify({
                'success': False,
                'error': 'Service management not available on this platform'
            }), 501
        
        status = service_manager.get_service_status()
        
        return jsonify({
            'success': True,
            'data': status
        })
        
    except Exception as e:
        logger.error(f"Failed to get service status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@service_mgmt_bp.route('/start', methods=['POST'])
def start_service():
    """Start the service"""
    try:
        service_manager = get_service_manager()
        if not service_manager:
            return jsonify({
                'success': False,
                'error': 'Service management not available on this platform'
            }), 501
        
        if service_manager.start_service():
            return jsonify({
                'success': True,
                'message': 'Service started successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to start service'
            }), 500
            
    except Exception as e:
        logger.error(f"Failed to start service: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@service_mgmt_bp.route('/stop', methods=['POST'])
def stop_service():
    """Stop the service"""
    try:
        service_manager = get_service_manager()
        if not service_manager:
            return jsonify({
                'success': False,
                'error': 'Service management not available on this platform'
            }), 501
        
        if service_manager.stop_service():
            return jsonify({
                'success': True,
                'message': 'Service stopped successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to stop service'
            }), 500
            
    except Exception as e:
        logger.error(f"Failed to stop service: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@service_mgmt_bp.route('/restart', methods=['POST'])
def restart_service():
    """Restart the service"""
    try:
        service_manager = get_service_manager()
        if not service_manager:
            return jsonify({
                'success': False,
                'error': 'Service management not available on this platform'
            }), 501
        
        if service_manager.restart_service():
            return jsonify({
                'success': True,
                'message': 'Service restarted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to restart service'
            }), 500
            
    except Exception as e:
        logger.error(f"Failed to restart service: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@service_mgmt_bp.route('/install', methods=['POST'])
def install_service():
    """Install service for auto-start"""
    try:
        service_manager = get_service_manager()
        if not service_manager:
            return jsonify({
                'success': False,
                'error': 'Service management not available on this platform'
            }), 501
        
        if service_manager.install_service():
            return jsonify({
                'success': True,
                'message': 'Service installed successfully for auto-start'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to install service'
            }), 500
            
    except Exception as e:
        logger.error(f"Failed to install service: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@service_mgmt_bp.route('/uninstall', methods=['POST'])
def uninstall_service():
    """Uninstall service"""
    try:
        service_manager = get_service_manager()
        if not service_manager:
            return jsonify({
                'success': False,
                'error': 'Service management not available on this platform'
            }), 501
        
        if service_manager.uninstall_service():
            return jsonify({
                'success': True,
                'message': 'Service uninstalled successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to uninstall service'
            }), 500
            
    except Exception as e:
        logger.error(f"Failed to uninstall service: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@service_mgmt_bp.route('/config', methods=['GET'])
def get_service_config():
    """Get service configuration"""
    try:
        service_manager = get_service_manager()
        if not service_manager:
            return jsonify({
                'success': False,
                'error': 'Service management not available on this platform'
            }), 501
        
        return jsonify({
            'success': True,
            'data': service_manager.config
        })
        
    except Exception as e:
        logger.error(f"Failed to get service config: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@service_mgmt_bp.route('/config', methods=['POST'])
def update_service_config():
    """Update service configuration"""
    try:
        service_manager = get_service_manager()
        if not service_manager:
            return jsonify({
                'success': False,
                'error': 'Service management not available on this platform'
            }), 501
        
        data = request.get_json() or {}
        
        # Validate configuration keys
        valid_keys = {
            'auto_start', 'minimize_to_tray', 'start_minimized', 
            'port', 'log_level', 'update_check', 'notifications'
        }
        
        config_updates = {k: v for k, v in data.items() if k in valid_keys}
        
        if not config_updates:
            return jsonify({
                'success': False,
                'error': 'No valid configuration keys provided'
            }), 400
        
        service_manager.update_config(**config_updates)
        
        return jsonify({
            'success': True,
            'message': 'Configuration updated successfully',
            'data': service_manager.config
        })
        
    except Exception as e:
        logger.error(f"Failed to update service config: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@service_mgmt_bp.route('/open-app', methods=['POST'])
def open_application():
    """Open the application in browser"""
    try:
        service_manager = get_service_manager()
        if not service_manager:
            return jsonify({
                'success': False,
                'error': 'Service management not available on this platform'
            }), 501
        
        service_manager.open_app()
        
        return jsonify({
            'success': True,
            'message': 'Application opened in browser'
        })
        
    except Exception as e:
        logger.error(f"Failed to open application: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@service_mgmt_bp.route('/show-in-finder', methods=['POST'])
def show_in_finder():
    """Show application directory in Finder"""
    try:
        service_manager = get_service_manager()
        if not service_manager:
            return jsonify({
                'success': False,
                'error': 'Service management not available on this platform'
            }), 501
        
        service_manager.show_in_finder()
        
        return jsonify({
            'success': True,
            'message': 'Application directory opened in Finder'
        })
        
    except Exception as e:
        logger.error(f"Failed to show in Finder: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@service_mgmt_bp.route('/create-app-bundle', methods=['POST'])
def create_app_bundle():
    """Create macOS app bundle"""
    try:
        from src.macos_service_integration import create_app_bundle
        
        bundle_path = create_app_bundle()
        
        return jsonify({
            'success': True,
            'message': 'App bundle created successfully',
            'data': {
                'bundle_path': str(bundle_path)
            }
        })
        
    except ImportError:
        return jsonify({
            'success': False,
            'error': 'App bundle creation not available on this platform'
        }), 501
    except Exception as e:
        logger.error(f"Failed to create app bundle: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@service_mgmt_bp.route('/tray/minimize', methods=['POST'])
def minimize_to_tray():
    """Minimize application to system tray"""
    try:
        service_manager = get_service_manager()
        if not service_manager:
            return jsonify({
                'success': False,
                'error': 'Service management not available on this platform'
            }), 501
        
        from src.macos_service_integration import SystemTrayIntegration
        tray_integration = SystemTrayIntegration(service_manager)
        
        if tray_integration.minimize_to_tray():
            return jsonify({
                'success': True,
                'message': 'Application minimized to system tray'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Minimize to tray is disabled'
            }), 400
            
    except Exception as e:
        logger.error(f"Failed to minimize to tray: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@service_mgmt_bp.route('/tray/restore', methods=['POST'])
def restore_from_tray():
    """Restore application from system tray"""
    try:
        service_manager = get_service_manager()
        if not service_manager:
            return jsonify({
                'success': False,
                'error': 'Service management not available on this platform'
            }), 501
        
        from src.macos_service_integration import SystemTrayIntegration
        tray_integration = SystemTrayIntegration(service_manager)
        
        if tray_integration.restore_from_tray():
            return jsonify({
                'success': True,
                'message': 'Application restored from system tray'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Application is not in system tray'
            }), 400
            
    except Exception as e:
        logger.error(f"Failed to restore from tray: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@service_mgmt_bp.route('/platform-info', methods=['GET'])
def get_platform_info():
    """Get platform and service availability information"""
    try:
        import platform
        
        platform_info = {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor()
        }
        
        # Check service availability
        service_available = False
        try:
            from src.macos_service_integration import MacOSServiceManager
            service_available = platform.system() == 'Darwin'  # macOS
        except ImportError:
            pass
        
        return jsonify({
            'success': True,
            'data': {
                'platform': platform_info,
                'service_available': service_available,
                'features': {
                    'auto_start': service_available,
                    'system_tray': service_available,
                    'app_bundle': service_available,
                    'launch_agent': service_available
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get platform info: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

