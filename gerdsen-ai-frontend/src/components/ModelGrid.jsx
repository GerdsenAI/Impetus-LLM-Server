import React, { useState, useEffect } from 'react';
import ModelCard from './ModelCard';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { 
  RefreshCw, 
  Search, 
  Filter, 
  Grid3X3, 
  List,
  Plus,
  Download,
  FolderOpen,
  Loader,
  AlertCircle
} from 'lucide-react';

const ModelGrid = ({ 
  serverUrl = 'http://localhost:8080',
  onModelLoad,
  onModelUnload,
  onModelSwitch,
  onModelDelete,
  onAddModel
}) => {
  const [models, setModels] = useState([]);
  const [filteredModels, setFilteredModels] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFormat, setSelectedFormat] = useState('all');
  const [selectedCapability, setSelectedCapability] = useState('all');
  const [viewMode, setViewMode] = useState('grid'); // 'grid' or 'list'
  const [activeModel, setActiveModel] = useState(null);
  const [loadingModels, setLoadingModels] = useState({}); // Use object instead of Set for better React state handling

  // Available formats and capabilities for filtering
  const [availableFormats, setAvailableFormats] = useState(['all']);
  const [availableCapabilities, setAvailableCapabilities] = useState(['all']);

  // Fetch models from server
  const fetchModels = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Scan for models
      const scanResponse = await fetch(`${serverUrl}/api/models/scan`);
      const scanData = await scanResponse.json();
      
      if (scanData.success !== false) {
        let modelsList = [];
        
        // Handle different response formats
        if (Array.isArray(scanData.models)) {
          modelsList = scanData.models;
        } else if (typeof scanData.models === 'object') {
          // Flatten format-based object structure
          modelsList = Object.values(scanData.models).flat();
        }
        
        // Transform models to consistent format
        const transformedModels = modelsList.map((model, index) => ({
          id: model.id || model.name || `model-${index}`,
          name: model.name || model.id || 'Unknown Model',
          format: model.format || 'unknown',
          capabilities: model.capabilities || model.capability ? [model.capability] : ['general'],
          size_gb: model.size_gb || (model.sizeMB ? model.sizeMB / 1024 : null),
          sizeMB: model.sizeMB || (model.size ? model.size / (1024 * 1024) : null),
          path: model.path,
          status: model.status || 'available',
          description: model.description,
          parameters: model.parameters,
          quantization: model.quantization,
          modified: model.modified
        }));

        setModels(transformedModels);
        
        // Update available filters
        const formats = [...new Set(transformedModels.map(m => m.format))];
        const capabilities = [...new Set(transformedModels.flatMap(m => m.capabilities))];
        
        setAvailableFormats(['all', ...formats]);
        setAvailableCapabilities(['all', ...capabilities]);
      } else {
        setModels([]);
      }
    } catch (err) {
      console.error('Error fetching models:', err);
      setError(`Failed to fetch models: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Filter models based on search and filters
  useEffect(() => {
    let filtered = models;

    // Text search
    if (searchTerm) {
      filtered = filtered.filter(model => 
        model.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        model.format.toLowerCase().includes(searchTerm.toLowerCase()) ||
        model.capabilities.some(cap => cap.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }

    // Format filter
    if (selectedFormat !== 'all') {
      filtered = filtered.filter(model => model.format === selectedFormat);
    }

    // Capability filter
    if (selectedCapability !== 'all') {
      filtered = filtered.filter(model => 
        model.capabilities.includes(selectedCapability)
      );
    }

    setFilteredModels(filtered);
  }, [models, searchTerm, selectedFormat, selectedCapability]);

  // Load initial models
  useEffect(() => {
    fetchModels();
  }, []);

  // Handle model actions
  const handleModelLoad = async (modelId) => {
    const model = models.find(m => m.id === modelId);
    if (!model) return;

    setLoadingModels(prev => ({ ...prev, [modelId]: true }));
    
    try {
      const response = await fetch(`${serverUrl}/api/models/load`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          path: model.path,
          id: modelId
        }),
      });

      const result = await response.json();
      
      if (response.ok) {
        // Update model status
        setModels(prev => prev.map(m => 
          m.id === modelId ? { ...m, status: 'loaded' } : m
        ));
        onModelLoad?.(modelId, result);
      } else {
        throw new Error(result.error || 'Failed to load model');
      }
    } catch (err) {
      console.error('Error loading model:', err);
      setError(`Failed to load model: ${err.message}`);
    } finally {
      setLoadingModels(prev => {
        const newState = { ...prev };
        delete newState[modelId];
        return newState;
      });
    }
  };

  const handleModelUnload = async (modelId) => {
    try {
      const response = await fetch(`${serverUrl}/api/models/${modelId}/unload`, {
        method: 'POST',
      });

      if (response.ok) {
        setModels(prev => prev.map(m => 
          m.id === modelId ? { ...m, status: 'available' } : m
        ));
        if (activeModel === modelId) {
          setActiveModel(null);
        }
        onModelUnload?.(modelId);
      }
    } catch (err) {
      console.error('Error unloading model:', err);
      setError(`Failed to unload model: ${err.message}`);
    }
  };

  const handleModelSwitch = async (modelId) => {
    try {
      const response = await fetch(`${serverUrl}/v1/models/${modelId}/switch`, {
        method: 'POST',
      });

      if (response.ok) {
        setActiveModel(modelId);
        onModelSwitch?.(modelId);
      }
    } catch (err) {
      console.error('Error switching model:', err);
      setError(`Failed to switch model: ${err.message}`);
    }
  };

  const handleModelDelete = async (modelId) => {
    if (window.confirm('Are you sure you want to delete this model? This action cannot be undone.')) {
      try {
        // For now, just remove from local state
        // In a real implementation, this might delete the file
        setModels(prev => prev.filter(m => m.id !== modelId));
        onModelDelete?.(modelId);
      } catch (err) {
        console.error('Error deleting model:', err);
        setError(`Failed to delete model: ${err.message}`);
      }
    }
  };

  const handleOpenModelsDirectory = async () => {
    try {
      const response = await fetch(`${serverUrl}/api/models/directory`);
      const result = await response.json();
      
      if (result.success) {
        // This would ideally open the file manager
        // For now, just show the directory path
        alert(`Models directory: ${result.directory}`);
      }
    } catch (err) {
      console.error('Error opening models directory:', err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Model Library</h2>
          <p className="text-gray-600">
            {filteredModels.length} of {models.length} models
          </p>
        </div>
        
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={fetchModels}
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          
          <Button variant="outline" onClick={handleOpenModelsDirectory}>
            <FolderOpen className="h-4 w-4 mr-2" />
            Open Directory
          </Button>
          
          <Button onClick={onAddModel}>
            <Plus className="h-4 w-4 mr-2" />
            Add Model
          </Button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col lg:flex-row gap-4 items-start lg:items-center justify-between">
        <div className="flex flex-col sm:flex-row gap-3 flex-1">
          {/* Search */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Search models..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Format Filter */}
          <select
            value={selectedFormat}
            onChange={(e) => setSelectedFormat(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md bg-white text-sm"
          >
            {availableFormats.map(format => (
              <option key={format} value={format}>
                {format === 'all' ? 'All Formats' : format.toUpperCase()}
              </option>
            ))}
          </select>

          {/* Capability Filter */}
          <select
            value={selectedCapability}
            onChange={(e) => setSelectedCapability(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md bg-white text-sm"
          >
            {availableCapabilities.map(capability => (
              <option key={capability} value={capability}>
                {capability === 'all' ? 'All Capabilities' : capability}
              </option>
            ))}
          </select>
        </div>

        {/* View Mode Toggle */}
        <div className="flex border border-gray-300 rounded-md overflow-hidden">
          <Button
            variant={viewMode === 'grid' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setViewMode('grid')}
            className="rounded-none"
          >
            <Grid3X3 className="h-4 w-4" />
          </Button>
          <Button
            variant={viewMode === 'list' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setViewMode('list')}
            className="rounded-none"
          >
            <List className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Active Filters */}
      {(selectedFormat !== 'all' || selectedCapability !== 'all' || searchTerm) && (
        <div className="flex flex-wrap gap-2">
          <span className="text-sm text-gray-600">Active filters:</span>
          {searchTerm && (
            <Badge variant="secondary" className="cursor-pointer" onClick={() => setSearchTerm('')}>
              Search: {searchTerm} ×
            </Badge>
          )}
          {selectedFormat !== 'all' && (
            <Badge variant="secondary" className="cursor-pointer" onClick={() => setSelectedFormat('all')}>
              Format: {selectedFormat.toUpperCase()} ×
            </Badge>
          )}
          {selectedCapability !== 'all' && (
            <Badge variant="secondary" className="cursor-pointer" onClick={() => setSelectedCapability('all')}>
              Capability: {selectedCapability} ×
            </Badge>
          )}
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-md text-red-700">
          <AlertCircle className="h-4 w-4" />
          {error}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <Loader className="h-8 w-8 animate-spin" />
          <span className="ml-2">Loading models...</span>
        </div>
      )}

      {/* Models Grid/List */}
      {!loading && filteredModels.length > 0 && (
        <div className={
          viewMode === 'grid' 
            ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4'
            : 'space-y-4'
        }>
          {filteredModels.map((model) => (
            <ModelCard
              key={model.id}
              model={model}
              isActive={activeModel === model.id}
              isLoading={!!loadingModels[model.id]}
              onLoad={handleModelLoad}
              onUnload={handleModelUnload}
              onSwitch={handleModelSwitch}
              onDelete={handleModelDelete}
              onGetInfo={(modelId) => {
                // Show model info modal
                console.log('Show info for:', modelId);
              }}
            />
          ))}
        </div>
      )}

      {/* Empty State */}
      {!loading && filteredModels.length === 0 && models.length === 0 && (
        <div className="text-center py-12">
          <Download className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No models found</h3>
          <p className="text-gray-600 mb-4">
            Add some models to your library to get started.
          </p>
          <div className="space-x-2">
            <Button onClick={onAddModel}>
              <Plus className="h-4 w-4 mr-2" />
              Add Model
            </Button>
            <Button variant="outline" onClick={handleOpenModelsDirectory}>
              <FolderOpen className="h-4 w-4 mr-2" />
              Open Models Directory
            </Button>
          </div>
        </div>
      )}

      {/* No Results State */}
      {!loading && filteredModels.length === 0 && models.length > 0 && (
        <div className="text-center py-8">
          <Search className="h-8 w-8 text-gray-400 mx-auto mb-2" />
          <h3 className="text-lg font-medium text-gray-900 mb-1">No matching models</h3>
          <p className="text-gray-600">
            Try adjusting your search terms or filters.
          </p>
        </div>
      )}
    </div>
  );
};

export default ModelGrid;