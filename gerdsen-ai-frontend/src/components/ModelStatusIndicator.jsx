import React, { useEffect, useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  Loader,
  CheckCircle,
  AlertCircle,
  Clock,
  Cpu,
  Zap,
  WifiOff
} from 'lucide-react';

const ModelStatusIndicator = ({ 
  modelId, 
  status, 
  progress = 0,
  isActive = false,
  showDetails = true
}) => {
  const [animatedProgress, setAnimatedProgress] = useState(0);

  // Smooth progress animation
  useEffect(() => {
    const timer = setTimeout(() => {
      setAnimatedProgress(progress);
    }, 100);
    return () => clearTimeout(timer);
  }, [progress]);

  const getStatusConfig = () => {
    const baseStatus = typeof status === 'object' ? status.status : status;
    
    switch (baseStatus) {
      case 'loading':
        return {
          icon: <Loader className="h-4 w-4 animate-spin" />,
          color: 'bg-blue-100 text-blue-800 border-blue-200',
          text: 'Loading',
          showProgress: true
        };
      
      case 'loaded':
        return {
          icon: <CheckCircle className="h-4 w-4" />,
          color: 'bg-green-100 text-green-800 border-green-200',
          text: isActive ? 'Active' : 'Loaded',
          showProgress: false
        };
      
      case 'unloading':
        return {
          icon: <Loader className="h-4 w-4 animate-spin" />,
          color: 'bg-orange-100 text-orange-800 border-orange-200',
          text: 'Unloading',
          showProgress: false
        };
      
      case 'error':
        return {
          icon: <AlertCircle className="h-4 w-4" />,
          color: 'bg-red-100 text-red-800 border-red-200',
          text: 'Error',
          showProgress: false
        };
      
      case 'queued':
        return {
          icon: <Clock className="h-4 w-4" />,
          color: 'bg-yellow-100 text-yellow-800 border-yellow-200',
          text: 'Queued',
          showProgress: false
        };
      
      case 'processing':
        return {
          icon: <Cpu className="h-4 w-4 animate-pulse" />,
          color: 'bg-purple-100 text-purple-800 border-purple-200',
          text: 'Processing',
          showProgress: true
        };
      
      case 'ready':
        return {
          icon: <Zap className="h-4 w-4" />,
          color: 'bg-indigo-100 text-indigo-800 border-indigo-200',
          text: 'Ready',
          showProgress: false
        };
      
      case 'offline':
        return {
          icon: <WifiOff className="h-4 w-4" />,
          color: 'bg-gray-100 text-gray-800 border-gray-200',
          text: 'Offline',
          showProgress: false
        };
      
      default:
        return {
          icon: <Clock className="h-4 w-4" />,
          color: 'bg-gray-100 text-gray-800 border-gray-200',
          text: baseStatus || 'Unknown',
          showProgress: false
        };
    }
  };

  const config = getStatusConfig();
  const currentProgress = typeof status === 'object' ? status.progress : progress;

  if (!showDetails) {
    return (
      <div className="flex items-center gap-1">
        {config.icon}
        {isActive && <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <Badge variant="outline" className={`flex items-center gap-1 ${config.color}`}>
          {config.icon}
          <span>{config.text}</span>
        </Badge>
        {isActive && (
          <Badge className="bg-blue-500 text-white text-xs">
            Active
          </Badge>
        )}
      </div>
      
      {config.showProgress && currentProgress > 0 && (
        <div className="space-y-1">
          <div className="flex justify-between text-xs text-gray-600">
            <span>Progress</span>
            <span>{Math.round(currentProgress)}%</span>
          </div>
          <Progress 
            value={animatedProgress} 
            className="h-2 transition-all duration-300"
          />
        </div>
      )}
    </div>
  );
};

export default ModelStatusIndicator;