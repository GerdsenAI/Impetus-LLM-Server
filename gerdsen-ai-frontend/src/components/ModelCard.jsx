import React from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Play, 
  Pause, 
  Download, 
  Trash2, 
  Info, 
  Cpu, 
  HardDrive, 
  Clock,
  CheckCircle,
  AlertCircle,
  Loader
} from 'lucide-react';

const ModelCard = ({ 
  model, 
  isActive = false, 
  isLoading = false,
  onLoad,
  onUnload,
  onDelete,
  onGetInfo,
  onSwitch
}) => {
  const getStatusIcon = () => {
    if (isLoading) return <Loader className="h-4 w-4 animate-spin" />;
    if (model.status === 'loaded') return <CheckCircle className="h-4 w-4 text-green-500" />;
    if (model.status === 'error') return <AlertCircle className="h-4 w-4 text-red-500" />;
    return <Clock className="h-4 w-4 text-gray-400" />;
  };

  const getStatusColor = () => {
    if (model.status === 'loaded') return 'bg-green-100 text-green-800 border-green-200';
    if (model.status === 'error') return 'bg-red-100 text-red-800 border-red-200';
    if (model.status === 'loading') return 'bg-blue-100 text-blue-800 border-blue-200';
    return 'bg-gray-100 text-gray-800 border-gray-200';
  };

  const formatSize = (bytes) => {
    if (!bytes) return 'Unknown';
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 Bytes';
    const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const formatCapabilities = (capabilities) => {
    if (!capabilities || capabilities.length === 0) return ['General'];
    return capabilities;
  };

  return (
    <Card className={`relative transition-all duration-200 hover:shadow-lg ${
      isActive ? 'ring-2 ring-blue-500 shadow-lg' : ''
    }`}>
      {isActive && (
        <div className="absolute -top-2 -right-2 z-10">
          <Badge className="bg-blue-500 text-white">Active</Badge>
        </div>
      )}
      
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <CardTitle className="text-lg font-semibold truncate">
              {model.name || model.id}
            </CardTitle>
            <CardDescription className="text-sm text-gray-600 mt-1">
              {model.description || `${model.format?.toUpperCase()} model`}
            </CardDescription>
          </div>
          <div className="flex items-center gap-2 ml-2">
            {getStatusIcon()}
            <Badge variant="outline" className={getStatusColor()}>
              {model.status || 'Unknown'}
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {/* Format and Capabilities */}
        <div className="flex flex-wrap gap-2">
          <Badge variant="secondary" className="text-xs">
            {model.format?.toUpperCase() || 'Unknown Format'}
          </Badge>
          {formatCapabilities(model.capabilities).map((capability, index) => (
            <Badge key={index} variant="outline" className="text-xs">
              {capability}
            </Badge>
          ))}
        </div>

        {/* Model Details */}
        <div className="grid grid-cols-2 gap-3 text-sm">
          {model.parameters && (
            <div className="flex items-center gap-1 text-gray-600">
              <Cpu className="h-3 w-3" />
              <span>{model.parameters}</span>
            </div>
          )}
          
          {(model.size_gb || model.sizeMB) && (
            <div className="flex items-center gap-1 text-gray-600">
              <HardDrive className="h-3 w-3" />
              <span>
                {model.size_gb 
                  ? `${model.size_gb.toFixed(1)} GB`
                  : formatSize(model.sizeMB * 1024 * 1024)
                }
              </span>
            </div>
          )}

          {model.quantization && (
            <div className="text-gray-600">
              <span className="font-medium">Quantization:</span> {model.quantization}
            </div>
          )}

          {model.load_time && (
            <div className="flex items-center gap-1 text-gray-600">
              <Clock className="h-3 w-3" />
              <span>{model.load_time.toFixed(1)}s load</span>
            </div>
          )}
        </div>

        {/* Performance Metrics */}
        {model.memory_usage_mb && (
          <div className="text-sm">
            <div className="flex justify-between text-gray-600">
              <span>Memory Usage</span>
              <span>{formatSize(model.memory_usage_mb * 1024 * 1024)}</span>
            </div>
            {model.memory_usage_mb > 0 && (
              <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                <div 
                  className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                  style={{ 
                    width: `${Math.min((model.memory_usage_mb / 8192) * 100, 100)}%` 
                  }}
                />
              </div>
            )}
          </div>
        )}

        {/* File Path */}
        {model.path && (
          <div className="text-xs text-gray-500 truncate" title={model.path}>
            📁 {model.path}
          </div>
        )}
      </CardContent>

      <CardFooter className="pt-3 space-x-2">
        {model.status === 'loaded' ? (
          <>
            {!isActive && (
              <Button 
                size="sm" 
                onClick={() => onSwitch?.(model.id)}
                className="flex-1"
              >
                <Play className="h-3 w-3 mr-1" />
                Switch To
              </Button>
            )}
            {isActive && (
              <Button 
                size="sm" 
                variant="outline"
                className="flex-1"
                disabled
              >
                <CheckCircle className="h-3 w-3 mr-1" />
                Active
              </Button>
            )}
            <Button 
              size="sm" 
              variant="outline"
              onClick={() => onUnload?.(model.id)}
            >
              <Pause className="h-3 w-3" />
            </Button>
          </>
        ) : (
          <Button 
            size="sm" 
            onClick={() => onLoad?.(model.id)}
            disabled={isLoading || model.status === 'loading'}
            className="flex-1"
          >
            {isLoading ? (
              <Loader className="h-3 w-3 mr-1 animate-spin" />
            ) : (
              <Download className="h-3 w-3 mr-1" />
            )}
            {isLoading ? 'Loading...' : 'Load Model'}
          </Button>
        )}
        
        <Button 
          size="sm" 
          variant="outline"
          onClick={() => onGetInfo?.(model.id)}
        >
          <Info className="h-3 w-3" />
        </Button>
        
        <Button 
          size="sm" 
          variant="outline"
          onClick={() => onDelete?.(model.id)}
          className="text-red-600 hover:text-red-700 hover:bg-red-50"
        >
          <Trash2 className="h-3 w-3" />
        </Button>
      </CardFooter>
    </Card>
  );
};

export default ModelCard;