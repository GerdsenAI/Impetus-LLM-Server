import React, { useState, useCallback, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Search, 
  Download, 
  X, 
  ChevronRight,
  HardDrive,
  Cpu,
  Filter,
  AlertCircle,
  CheckCircle,
  Loader
} from 'lucide-react';

const ModelSearch = ({ 
  serverUrl = 'http://localhost:8080',
  onDownloadComplete,
  onDownloadError
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState({});
  const [error, setError] = useState(null);
  const [selectedTask, setSelectedTask] = useState('text-generation');
  const [sortBy, setSortBy] = useState('downloads');

  // Popular model suggestions
  const popularModels = [
    { id: 'TheBloke/CodeLlama-13B-Instruct-GGUF', name: 'CodeLlama 13B Instruct', format: 'GGUF' },
    { id: 'TheBloke/Mistral-7B-Instruct-v0.2-GGUF', name: 'Mistral 7B Instruct v0.2', format: 'GGUF' },
    { id: 'TheBloke/Llama-2-7B-Chat-GGUF', name: 'Llama 2 7B Chat', format: 'GGUF' },
    { id: 'microsoft/phi-2', name: 'Phi-2', format: 'SafeTensors' },
    { id: 'TinyLlama/TinyLlama-1.1B-Chat-v1.0', name: 'TinyLlama 1.1B Chat', format: 'SafeTensors' }
  ];

  // Task categories for filtering
  const taskCategories = [
    { value: 'text-generation', label: 'Text Generation' },
    { value: 'text2text-generation', label: 'Text to Text' },
    { value: 'feature-extraction', label: 'Embeddings' },
    { value: 'question-answering', label: 'Q&A' },
    { value: 'conversational', label: 'Conversational' }
  ];

  // Search HuggingFace models
  const searchModels = async () => {
    if (!searchQuery.trim() && selectedTask === 'text-generation') {
      // Show popular models if no search query
      setSearchResults(popularModels.map((model, index) => ({
        ...model,
        downloads: 1000000 - index * 100000,
        likes: 1000 - index * 100,
        size: `${(index + 1) * 2} GB`
      })));
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        query: searchQuery,
        task: selectedTask,
        sort: sortBy,
        limit: '20'
      });

      const response = await fetch(`${serverUrl}/api/models/search?${params}`);
      const data = await response.json();

      if (response.ok && data.models) {
        setSearchResults(data.models);
      } else {
        throw new Error(data.error || 'Failed to search models');
      }
    } catch (err) {
      console.error('Search error:', err);
      setError(err.message);
      // Fallback to showing popular models on error
      setSearchResults(popularModels.map((model, index) => ({
        ...model,
        downloads: 1000000 - index * 100000,
        likes: 1000 - index * 100,
        size: `${(index + 1) * 2} GB`
      })));
    } finally {
      setLoading(false);
    }
  };

  // Download model from HuggingFace
  const downloadModel = async (modelId, modelInfo) => {
    setDownloading(prev => ({ ...prev, [modelId]: { progress: 0, status: 'starting' } }));

    try {
      const response = await fetch(`${serverUrl}/api/models/download`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model_id: modelId,
          format: modelInfo.format || 'auto'
        }),
      });

      if (!response.ok) {
        throw new Error('Download failed');
      }

      // Set up event source for progress updates
      const eventSource = new EventSource(`${serverUrl}/api/models/download/${modelId}/progress`);

      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.status === 'downloading') {
          setDownloading(prev => ({
            ...prev,
            [modelId]: { progress: data.progress, status: 'downloading' }
          }));
        } else if (data.status === 'completed') {
          setDownloading(prev => {
            const newState = { ...prev };
            delete newState[modelId];
            return newState;
          });
          eventSource.close();
          onDownloadComplete?.(modelId, data);
        } else if (data.status === 'error') {
          setDownloading(prev => {
            const newState = { ...prev };
            delete newState[modelId];
            return newState;
          });
          eventSource.close();
          onDownloadError?.(modelId, new Error(data.error));
        }
      };

      eventSource.onerror = () => {
        eventSource.close();
        setDownloading(prev => {
          const newState = { ...prev };
          delete newState[modelId];
          return newState;
        });
        onDownloadError?.(modelId, new Error('Download connection lost'));
      };

    } catch (err) {
      console.error('Download error:', err);
      setDownloading(prev => {
        const newState = { ...prev };
        delete newState[modelId];
        return newState;
      });
      onDownloadError?.(modelId, err);
    }
  };

  // Cancel download
  const cancelDownload = async (modelId) => {
    try {
      await fetch(`${serverUrl}/api/models/download/${modelId}/cancel`, {
        method: 'POST'
      });
      
      setDownloading(prev => {
        const newState = { ...prev };
        delete newState[modelId];
        return newState;
      });
    } catch (err) {
      console.error('Cancel error:', err);
    }
  };

  // Format file size
  const formatSize = (sizeStr) => {
    if (!sizeStr) return 'Unknown size';
    return sizeStr;
  };

  // Format download count
  const formatDownloads = (count) => {
    if (!count) return '0';
    if (count >= 1000000) return `${(count / 1000000).toFixed(1)}M`;
    if (count >= 1000) return `${(count / 1000).toFixed(1)}K`;
    return count.toString();
  };

  // Search on mount and when filters change
  useEffect(() => {
    searchModels();
  }, [selectedTask, sortBy]);

  return (
    <div className="space-y-4">
      {/* Search Bar */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search HuggingFace models..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && searchModels()}
            className="pl-10"
          />
        </div>
        <Button onClick={searchModels} disabled={loading}>
          {loading ? <Loader className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
          Search
        </Button>
      </div>

      {/* Filters */}
      <div className="flex gap-2 flex-wrap">
        <select
          value={selectedTask}
          onChange={(e) => setSelectedTask(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-md bg-white text-sm"
        >
          {taskCategories.map(task => (
            <option key={task.value} value={task.value}>
              {task.label}
            </option>
          ))}
        </select>

        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-md bg-white text-sm"
        >
          <option value="downloads">Most Downloads</option>
          <option value="likes">Most Likes</option>
          <option value="modified">Recently Updated</option>
        </select>
      </div>

      {/* Error Message */}
      {error && (
        <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-md text-red-700">
          <AlertCircle className="h-4 w-4" />
          {error}
        </div>
      )}

      {/* Search Results */}
      <ScrollArea className="h-[500px] pr-4">
        <div className="space-y-3">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader className="h-8 w-8 animate-spin" />
              <span className="ml-2">Searching models...</span>
            </div>
          ) : searchResults.length === 0 ? (
            <div className="text-center py-12">
              <Search className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No models found</h3>
              <p className="text-gray-600">Try adjusting your search terms or filters</p>
            </div>
          ) : (
            searchResults.map((model) => {
              const isDownloading = downloading[model.id];
              
              return (
                <Card key={model.id} className="hover:shadow-md transition-shadow">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <CardTitle className="text-base font-semibold truncate">
                          {model.name || model.id}
                        </CardTitle>
                        <CardDescription className="text-xs text-gray-600 mt-1">
                          {model.id}
                        </CardDescription>
                      </div>
                      <Badge variant="outline" className="ml-2">
                        {model.format || 'Unknown'}
                      </Badge>
                    </div>
                  </CardHeader>

                  <CardContent className="pb-3">
                    <div className="flex items-center gap-4 text-sm text-gray-600">
                      {model.downloads && (
                        <div className="flex items-center gap-1">
                          <Download className="h-3 w-3" />
                          <span>{formatDownloads(model.downloads)}</span>
                        </div>
                      )}
                      {model.likes && (
                        <div className="flex items-center gap-1">
                          <span>❤️</span>
                          <span>{model.likes}</span>
                        </div>
                      )}
                      {model.size && (
                        <div className="flex items-center gap-1">
                          <HardDrive className="h-3 w-3" />
                          <span>{formatSize(model.size)}</span>
                        </div>
                      )}
                    </div>

                    {isDownloading && (
                      <div className="mt-3">
                        <div className="flex items-center justify-between text-xs mb-1">
                          <span className="text-gray-600">
                            {isDownloading.status === 'starting' ? 'Starting download...' : 'Downloading...'}
                          </span>
                          <span className="text-gray-600">{isDownloading.progress}%</span>
                        </div>
                        <Progress value={isDownloading.progress} className="h-2" />
                      </div>
                    )}
                  </CardContent>

                  <CardFooter className="pt-3">
                    {isDownloading ? (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => cancelDownload(model.id)}
                        className="w-full"
                      >
                        <X className="h-3 w-3 mr-1" />
                        Cancel Download
                      </Button>
                    ) : (
                      <Button
                        size="sm"
                        onClick={() => downloadModel(model.id, model)}
                        className="w-full"
                      >
                        <Download className="h-3 w-3 mr-1" />
                        Download Model
                      </Button>
                    )}
                  </CardFooter>
                </Card>
              );
            })
          )}
        </div>
      </ScrollArea>

      {/* Popular Models Suggestion */}
      {searchResults.length === 0 && !loading && !searchQuery && (
        <div className="mt-6">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Popular Models to Get Started</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {popularModels.slice(0, 4).map(model => (
              <Button
                key={model.id}
                variant="outline"
                size="sm"
                onClick={() => setSearchQuery(model.id)}
                className="justify-start"
              >
                <ChevronRight className="h-3 w-3 mr-1" />
                {model.name}
              </Button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ModelSearch;