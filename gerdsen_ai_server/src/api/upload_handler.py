#!/usr/bin/env python3
"""
Secure file upload handler for model files
"""

import os
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

# Add parent directory to path for imports
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.file_security import (
    sanitize_filename, 
    is_safe_path, 
    validate_file_type,
    generate_safe_path,
    get_file_info
)
from utils.config import get_upload_config, get_env_bool

logger = logging.getLogger(__name__)

# Create Blueprint
upload_bp = Blueprint('upload', __name__)

class SecureUploadHandler:
    """Handles secure file uploads with validation and sanitization"""
    
    def __init__(self):
        config = get_upload_config()
        self.max_size_bytes = config['max_size_mb'] * 1024 * 1024
        self.allowed_extensions = config['allowed_extensions']
        self.upload_directory = os.path.expanduser(config['upload_directory'])
        
        # Ensure upload directory exists
        Path(self.upload_directory).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Upload handler initialized: max_size={config['max_size_mb']}MB, directory={self.upload_directory}")
    
    def validate_request(self, request) -> Tuple[bool, Optional[str]]:
        """Validate the upload request"""
        if 'model' not in request.files:
            return False, "No file provided in 'model' field"
        
        file = request.files['model']
        if file.filename == '':
            return False, "No file selected"
        
        # Check file size (if content length is available)
        if request.content_length and request.content_length > self.max_size_bytes:
            size_mb = request.content_length / (1024 * 1024)
            return False, f"File too large: {size_mb:.1f}MB exceeds maximum of {self.max_size_bytes / (1024 * 1024):.0f}MB"
        
        return True, None
    
    def process_upload(self, file) -> Dict[str, Any]:
        """Process the uploaded file securely"""
        original_filename = file.filename
        
        # Sanitize filename
        safe_filename = sanitize_filename(original_filename)
        
        # Validate file type
        is_valid, error_msg = validate_file_type(safe_filename, self.allowed_extensions)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Generate safe path
        try:
            final_path = generate_safe_path(self.upload_directory, safe_filename)
        except ValueError as e:
            raise ValueError(f"Invalid file path: {str(e)}")
        
        # Use temporary file for upload to prevent partial writes
        temp_fd, temp_path = tempfile.mkstemp(dir=self.upload_directory)
        
        try:
            # Save to temporary file with size checking
            bytes_written = 0
            chunk_size = 8192  # 8KB chunks
            
            with os.fdopen(temp_fd, 'wb') as temp_file:
                while True:
                    chunk = file.stream.read(chunk_size)
                    if not chunk:
                        break
                    
                    bytes_written += len(chunk)
                    
                    # Check size during upload
                    if bytes_written > self.max_size_bytes:
                        raise ValueError(f"File exceeds maximum size of {self.max_size_bytes / (1024 * 1024):.0f}MB")
                    
                    temp_file.write(chunk)
            
            # Move temporary file to final location
            shutil.move(temp_path, final_path)
            
            # Get file info
            file_info = get_file_info(final_path)
            
            return {
                'success': True,
                'message': 'File uploaded successfully',
                'file': {
                    'original_name': original_filename,
                    'saved_name': os.path.basename(final_path),
                    'path': final_path,
                    'size': file_info.get('size', bytes_written),
                    'size_mb': file_info.get('size', bytes_written) / (1024 * 1024),
                    'extension': file_info.get('extension', os.path.splitext(safe_filename)[1])
                }
            }
            
        except Exception as e:
            # Clean up temporary file on error
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except:
                pass
            
            raise e
        finally:
            # Ensure temp file descriptor is closed
            try:
                os.close(temp_fd)
            except:
                pass

# Create global handler instance
upload_handler = SecureUploadHandler()

@upload_bp.route('/api/models/upload', methods=['POST'])
def upload_model():
    """Secure model file upload endpoint"""
    try:
        # Validate request
        is_valid, error_msg = upload_handler.validate_request(request)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        # Process upload
        file = request.files['model']
        result = upload_handler.process_upload(file)
        
        # Log successful upload
        logger.info(f"Model uploaded successfully: {result['file']['saved_name']}")
        
        return jsonify(result), 200
        
    except ValueError as e:
        logger.warning(f"Upload validation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Upload failed. Please try again.'
        }), 500

@upload_bp.route('/api/models/upload/validate', methods=['POST'])
def validate_upload():
    """Validate upload parameters without actually uploading"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'valid': False,
                'error': 'No data provided'
            }), 400
        
        filename = data.get('filename', '')
        filesize = data.get('size', 0)
        
        # Validate filename
        if not filename:
            return jsonify({
                'valid': False,
                'error': 'No filename provided'
            })
        
        safe_filename = sanitize_filename(filename)
        is_valid, error_msg = validate_file_type(safe_filename, upload_handler.allowed_extensions)
        
        if not is_valid:
            return jsonify({
                'valid': False,
                'error': error_msg
            })
        
        # Validate size
        if filesize > upload_handler.max_size_bytes:
            return jsonify({
                'valid': False,
                'error': f'File too large: {filesize / (1024 * 1024):.1f}MB exceeds maximum'
            })
        
        return jsonify({
            'valid': True,
            'sanitized_filename': safe_filename,
            'max_size_mb': upload_handler.max_size_bytes / (1024 * 1024)
        })
        
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({
            'valid': False,
            'error': 'Validation failed'
        }), 500

def init_upload_routes(app):
    """Initialize upload routes with the Flask app"""
    app.register_blueprint(upload_bp)
    logger.info("Upload routes initialized")