import React, { useState, useRef, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { 
  Upload, 
  FileIcon, 
  X, 
  CheckCircle, 
  AlertCircle,
  Loader,
  FolderOpen,
  Download
} from 'lucide-react';

const DragDropZone = ({ 
  onFileUpload,
  onUploadComplete,
  onUploadError,
  serverUrl = 'http://localhost:8080',
  maxFileSize = 50 * 1024 * 1024 * 1024, // 50GB default
  acceptedFormats = ['.gguf', '.safetensors', '.mlx', '.bin', '.pt', '.pth', '.onnx', '.mlmodel', '.mlpackage']
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploadingFiles, setUploadingFiles] = useState([]);
  const [completedUploads, setCompletedUploads] = useState([]);
  const [errors, setErrors] = useState([]);
  const fileInputRef = useRef(null);

  // Supported file extensions and their descriptions
  const formatDescriptions = {
    '.gguf': 'GGUF - Quantized models (recommended)',
    '.safetensors': 'SafeTensors - Hugging Face standard',
    '.mlx': 'MLX - Apple Silicon optimized',
    '.bin': 'Binary format (PyTorch/Transformers)',
    '.pt': 'PyTorch format',
    '.pth': 'PyTorch checkpoint',
    '.onnx': 'ONNX - Cross-platform format',
    '.mlmodel': 'Core ML model',
    '.mlpackage': 'Core ML package'
  };

  const validateFile = (file) => {
    // Check file size
    if (file.size > maxFileSize) {
      return `File too large. Maximum size is ${formatBytes(maxFileSize)}`;
    }

    // Check file extension
    const extension = '.' + file.name.split('.').pop().toLowerCase();
    if (!acceptedFormats.includes(extension)) {
      return `Unsupported format. Accepted formats: ${acceptedFormats.join(', ')}`;
    }

    return null;
  };

  const formatBytes = (bytes, decimals = 2) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  };

  const uploadFile = async (file) => {
    const uploadId = Date.now() + Math.random();
    
    // Add to uploading files
    setUploadingFiles(prev => [...prev, {
      id: uploadId,
      file,
      progress: 0,
      status: 'uploading'
    }]);

    try {
      const formData = new FormData();
      formData.append('model', file);

      // Create XMLHttpRequest for progress tracking
      const xhr = new XMLHttpRequest();
      
      return new Promise((resolve, reject) => {
        xhr.upload.addEventListener('progress', (event) => {
          if (event.lengthComputable) {
            const progress = Math.round((event.loaded / event.total) * 100);
            setUploadingFiles(prev => prev.map(f => 
              f.id === uploadId ? { ...f, progress } : f
            ));
          }
        });

        xhr.addEventListener('load', () => {
          if (xhr.status === 200) {
            try {
              const response = JSON.parse(xhr.responseText);
              
              // Move to completed uploads
              setUploadingFiles(prev => prev.filter(f => f.id !== uploadId));
              setCompletedUploads(prev => [...prev, {
                id: uploadId,
                file,
                response,
                status: 'completed'
              }]);

              onUploadComplete?.(file, response);
              resolve(response);
            } catch (e) {
              reject(new Error('Invalid response from server'));
            }
          } else {
            try {
              const errorResponse = JSON.parse(xhr.responseText);
              reject(new Error(errorResponse.error || 'Upload failed'));
            } catch (e) {
              reject(new Error(`Upload failed with status ${xhr.status}`));
            }
          }
        });

        xhr.addEventListener('error', () => {
          reject(new Error('Network error during upload'));
        });

        xhr.addEventListener('abort', () => {
          reject(new Error('Upload cancelled'));
        });

        xhr.open('POST', `${serverUrl}/api/models/upload`);
        xhr.send(formData);
      });

    } catch (error) {
      // Remove from uploading files and add to errors
      setUploadingFiles(prev => prev.filter(f => f.id !== uploadId));
      setErrors(prev => [...prev, {
        id: uploadId,
        file,
        error: error.message
      }]);

      onUploadError?.(file, error);
      throw error;
    }
  };

  const handleFiles = async (files) => {
    const fileArray = Array.from(files);
    
    for (const file of fileArray) {
      const validationError = validateFile(file);
      
      if (validationError) {
        setErrors(prev => [...prev, {
          id: Date.now() + Math.random(),
          file,
          error: validationError
        }]);
        continue;
      }

      try {
        await uploadFile(file);
        onFileUpload?.(file);
      } catch (error) {
        console.error('Upload failed:', error);
      }
    }
  };

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFiles(files);
    }
  }, []);

  const handleFileInputChange = (e) => {
    const files = e.target.files;
    if (files.length > 0) {
      handleFiles(files);
    }
    // Reset input
    e.target.value = '';
  };

  const openFileDialog = () => {
    fileInputRef.current?.click();
  };

  const removeError = (errorId) => {
    setErrors(prev => prev.filter(e => e.id !== errorId));
  };

  const removeCompleted = (completedId) => {
    setCompletedUploads(prev => prev.filter(c => c.id !== completedId));
  };

  const cancelUpload = (uploadId) => {
    // In a real implementation, you'd cancel the XMLHttpRequest
    setUploadingFiles(prev => prev.filter(f => f.id !== uploadId));
  };

  return (
    <div className="space-y-4">
      {/* Drag & Drop Zone */}
      <div
        className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          isDragOver 
            ? 'border-blue-500 bg-blue-50' 
            : 'border-gray-300 hover:border-gray-400'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={acceptedFormats.join(',')}
          onChange={handleFileInputChange}
          className="hidden"
        />

        <div className="space-y-4">
          <div className="flex justify-center">
            <Upload className={`h-12 w-12 ${isDragOver ? 'text-blue-500' : 'text-gray-400'}`} />
          </div>
          
          <div>
            <h3 className="text-lg font-medium text-gray-900">
              {isDragOver ? 'Drop files here' : 'Upload Model Files'}
            </h3>
            <p className="text-gray-600 mt-1">
              Drag and drop model files here, or click to browse
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Button onClick={openFileDialog}>
              <FolderOpen className="h-4 w-4 mr-2" />
              Browse Files
            </Button>
            <Button variant="outline" onClick={() => window.open(`${serverUrl}/api/models/directory`)}>
              <Download className="h-4 w-4 mr-2" />
              Open Models Directory
            </Button>
          </div>
        </div>
      </div>

      {/* Supported Formats */}
      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-2">Supported Formats:</h4>
        <div className="flex flex-wrap gap-2">
          {acceptedFormats.map(format => (
            <Badge 
              key={format} 
              variant="outline" 
              className="text-xs"
              title={formatDescriptions[format]}
            >
              {format}
            </Badge>
          ))}
        </div>
      </div>

      {/* Uploading Files */}
      {uploadingFiles.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-gray-700">Uploading:</h4>
          {uploadingFiles.map(upload => (
            <div key={upload.id} className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg">
              <FileIcon className="h-5 w-5 text-blue-500" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{upload.file.name}</p>
                <p className="text-xs text-gray-500">{formatBytes(upload.file.size)}</p>
                <Progress value={upload.progress} className="mt-1" />
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500">{upload.progress}%</span>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => cancelUpload(upload.id)}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Completed Uploads */}
      {completedUploads.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-gray-700">Recently Uploaded:</h4>
          {completedUploads.map(completed => (
            <div key={completed.id} className="flex items-center gap-3 p-3 border border-green-200 bg-green-50 rounded-lg">
              <CheckCircle className="h-5 w-5 text-green-500" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{completed.file.name}</p>
                <p className="text-xs text-green-600">
                  Upload successful
                  {completed.response?.model_id && ` - Model ID: ${completed.response.model_id}`}
                </p>
              </div>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => removeCompleted(completed.id)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>
      )}

      {/* Errors */}
      {errors.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-red-700">Upload Errors:</h4>
          {errors.map(error => (
            <div key={error.id} className="flex items-center gap-3 p-3 border border-red-200 bg-red-50 rounded-lg">
              <AlertCircle className="h-5 w-5 text-red-500" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{error.file.name}</p>
                <p className="text-xs text-red-600">{error.error}</p>
              </div>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => removeError(error.id)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>
      )}

      {/* Usage Tips */}
      <div className="text-xs text-gray-500 space-y-1">
        <p><strong>Tips:</strong></p>
        <ul className="list-disc list-inside space-y-1">
          <li>GGUF files are recommended for best performance and compatibility</li>
          <li>Larger models may take several minutes to upload and load</li>
          <li>Models are automatically organized by format in your Models directory</li>
          <li>Maximum file size: {formatBytes(maxFileSize)}</li>
        </ul>
      </div>
    </div>
  );
};

export default DragDropZone;