#!/usr/bin/env python3
"""
WebSocket Routes for Real-time Updates
Provides real-time hardware monitoring and system updates via WebSocket
"""

from flask import Blueprint
from flask_socketio import SocketIO, emit, join_room, leave_room
import time
import threading
import logging
from typing import Dict, Any
from src.apple_silicon_detector import AppleSiliconDetector
from src.enhanced_mlx_manager import EnhancedMLXManager

# Global instances
socketio = None
detector = None
mlx_manager = None
active_connections = set()
monitoring_thread = None
monitoring_active = False

def init_websocket(app, socket_io):
    """Initialize WebSocket with Flask app"""
    global socketio, detector, mlx_manager
    socketio = socket_io
    detector = AppleSiliconDetector()
    mlx_manager = EnhancedMLXManager()
    
    # Register WebSocket events
    register_websocket_events()
    
    # Start monitoring thread
    start_monitoring_thread()
    
    logging.info("WebSocket initialized for real-time updates")

def register_websocket_events():
    """Register WebSocket event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        try:
            client_id = request.sid if 'request' in globals() else 'unknown'
            active_connections.add(client_id)
            
            # Send initial system information
            if detector:
                system_info = detector.get_comprehensive_info()
                emit('system_info', {
                    'success': True,
                    'data': system_info,
                    'timestamp': time.time()
                })
            
            logging.info(f"WebSocket client connected: {client_id}")
            
        except Exception as e:
            logging.error(f"Error handling WebSocket connection: {e}")
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        try:
            client_id = request.sid if 'request' in globals() else 'unknown'
            active_connections.discard(client_id)
            logging.info(f"WebSocket client disconnected: {client_id}")
            
        except Exception as e:
            logging.error(f"Error handling WebSocket disconnection: {e}")
    
    @socketio.on('subscribe_metrics')
    def handle_subscribe_metrics(data):
        """Handle subscription to real-time metrics"""
        try:
            client_id = request.sid if 'request' in globals() else 'unknown'
            join_room('metrics', client_id)
            
            # Send current metrics immediately
            if detector:
                metrics = detector.get_real_time_metrics()
                emit('metrics_update', {
                    'success': True,
                    'data': metrics,
                    'timestamp': time.time()
                })
            
            logging.info(f"Client subscribed to metrics: {client_id}")
            
        except Exception as e:
            logging.error(f"Error subscribing to metrics: {e}")
            emit('error', {'message': str(e)})
    
    @socketio.on('unsubscribe_metrics')
    def handle_unsubscribe_metrics():
        """Handle unsubscription from real-time metrics"""
        try:
            client_id = request.sid if 'request' in globals() else 'unknown'
            leave_room('metrics', client_id)
            logging.info(f"Client unsubscribed from metrics: {client_id}")
            
        except Exception as e:
            logging.error(f"Error unsubscribing from metrics: {e}")
    
    @socketio.on('subscribe_models')
    def handle_subscribe_models():
        """Handle subscription to model updates"""
        try:
            client_id = request.sid if 'request' in globals() else 'unknown'
            join_room('models', client_id)
            
            # Send current model status immediately
            if mlx_manager:
                model_status = get_model_status()
                emit('model_update', {
                    'success': True,
                    'data': model_status,
                    'timestamp': time.time()
                })
            
            logging.info(f"Client subscribed to model updates: {client_id}")
            
        except Exception as e:
            logging.error(f"Error subscribing to model updates: {e}")
            emit('error', {'message': str(e)})
    
    @socketio.on('unsubscribe_models')
    def handle_unsubscribe_models():
        """Handle unsubscription from model updates"""
        try:
            client_id = request.sid if 'request' in globals() else 'unknown'
            leave_room('models', client_id)
            logging.info(f"Client unsubscribed from model updates: {client_id}")
            
        except Exception as e:
            logging.error(f"Error unsubscribing from model updates: {e}")
    
    @socketio.on('get_hardware_info')
    def handle_get_hardware_info():
        """Handle request for hardware information"""
        try:
            if detector:
                hardware_info = {
                    'chip_info': detector.chip_info,
                    'neural_engine': detector.get_neural_engine_info(),
                    'gpu': detector.get_gpu_info(),
                    'system_info': detector.system_info
                }
                
                emit('hardware_info', {
                    'success': True,
                    'data': hardware_info,
                    'timestamp': time.time()
                })
            else:
                emit('error', {'message': 'Hardware detector not available'})
                
        except Exception as e:
            logging.error(f"Error getting hardware info: {e}")
            emit('error', {'message': str(e)})

def get_model_status() -> Dict[str, Any]:
    """Get current model status for WebSocket updates"""
    try:
        if not mlx_manager:
            return {}
        
        loaded_models = []
        for model_id, model_data in mlx_manager.loaded_models.items():
            model_info = mlx_manager.get_model_info(model_id)
            loaded_models.append({
                'id': model_id,
                'status': 'loaded',
                'info': model_info
            })
        
        return {
            'loaded_models': loaded_models,
            'total_loaded': len(loaded_models),
            'system_status': mlx_manager.get_system_status()
        }
        
    except Exception as e:
        logging.error(f"Error getting model status: {e}")
        return {}

def broadcast_metrics_update():
    """Broadcast real-time metrics to subscribed clients"""
    try:
        if not socketio or not detector:
            return
        
        metrics = detector.get_real_time_metrics()
        
        socketio.emit('metrics_update', {
            'success': True,
            'data': metrics,
            'timestamp': time.time()
        }, room='metrics')
        
    except Exception as e:
        logging.error(f"Error broadcasting metrics update: {e}")

def broadcast_model_update():
    """Broadcast model status updates to subscribed clients"""
    try:
        if not socketio or not mlx_manager:
            return
        
        model_status = get_model_status()
        
        socketio.emit('model_update', {
            'success': True,
            'data': model_status,
            'timestamp': time.time()
        }, room='models')
        
    except Exception as e:
        logging.error(f"Error broadcasting model update: {e}")

def broadcast_system_alert(alert_type: str, message: str, data: Dict[str, Any] = None):
    """Broadcast system alerts to all connected clients"""
    try:
        if not socketio:
            return
        
        alert = {
            'type': alert_type,
            'message': message,
            'data': data or {},
            'timestamp': time.time()
        }
        
        socketio.emit('system_alert', alert)
        logging.info(f"System alert broadcasted: {alert_type} - {message}")
        
    except Exception as e:
        logging.error(f"Error broadcasting system alert: {e}")

def monitoring_loop():
    """Main monitoring loop for real-time updates"""
    global monitoring_active
    
    last_metrics_broadcast = 0
    last_model_broadcast = 0
    last_thermal_check = 0
    
    while monitoring_active:
        try:
            current_time = time.time()
            
            # Broadcast metrics every second
            if current_time - last_metrics_broadcast >= 1.0:
                broadcast_metrics_update()
                last_metrics_broadcast = current_time
            
            # Broadcast model updates every 5 seconds
            if current_time - last_model_broadcast >= 5.0:
                broadcast_model_update()
                last_model_broadcast = current_time
            
            # Check thermal state every 10 seconds
            if current_time - last_thermal_check >= 10.0:
                check_thermal_alerts()
                last_thermal_check = current_time
            
            time.sleep(0.1)  # Small delay to prevent high CPU usage
            
        except Exception as e:
            logging.error(f"Error in monitoring loop: {e}")
            time.sleep(1)

def check_thermal_alerts():
    """Check for thermal alerts and broadcast warnings"""
    try:
        if not detector:
            return
        
        metrics = detector.get_real_time_metrics()
        thermal_info = metrics.get('thermal', {})
        
        thermal_state = thermal_info.get('state', 'unknown')
        temperatures = thermal_info.get('temperatures', {})
        
        # Check for thermal throttling
        if thermal_state == 'throttled':
            broadcast_system_alert(
                'thermal_warning',
                'System is thermal throttling - performance may be reduced',
                {'thermal_state': thermal_state, 'temperatures': temperatures}
            )
        
        # Check for high temperatures
        cpu_temp = temperatures.get('cpu_estimated', 0)
        if cpu_temp > 85:  # High temperature threshold
            broadcast_system_alert(
                'temperature_warning',
                f'High CPU temperature detected: {cpu_temp}°C',
                {'temperature': cpu_temp, 'component': 'cpu'}
            )
        
    except Exception as e:
        logging.error(f"Error checking thermal alerts: {e}")

def start_monitoring_thread():
    """Start the background monitoring thread"""
    global monitoring_thread, monitoring_active
    
    if monitoring_thread and monitoring_thread.is_alive():
        return
    
    monitoring_active = True
    monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
    monitoring_thread.start()
    
    logging.info("Real-time monitoring thread started")

def stop_monitoring_thread():
    """Stop the background monitoring thread"""
    global monitoring_active
    
    monitoring_active = False
    if monitoring_thread:
        monitoring_thread.join(timeout=2)
    
    logging.info("Real-time monitoring thread stopped")

# WebSocket blueprint for Flask registration
websocket_bp = Blueprint('websocket', __name__)

@websocket_bp.route('/status')
def websocket_status():
    """Get WebSocket service status"""
    return {
        'websocket_active': socketio is not None,
        'active_connections': len(active_connections),
        'monitoring_active': monitoring_active,
        'detector_available': detector is not None,
        'mlx_manager_available': mlx_manager is not None
    }

