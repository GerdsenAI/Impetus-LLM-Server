"""
Model Download Utilities for Impetus-LLM-Server
Handles downloading models from HuggingFace and other sources
"""

import os
import json
import time
import hashlib
import logging
import requests
from pathlib import Path
from typing import Dict, Optional, Callable, List, Tuple
from urllib.parse import urlparse, unquote
from tqdm import tqdm
from huggingface_hub import HfApi, hf_hub_download, list_repo_files
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class ModelDownloader:
    """Handle model downloads from various sources"""
    
    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = Path(cache_dir or os.path.expanduser("~/.cache/impetus-llm/models"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.hf_api = HfApi()
        self.download_progress = {}
        self.active_downloads = {}
        
    def download_model(self, 
                      model_id: str,
                      revision: Optional[str] = None,
                      patterns: Optional[List[str]] = None,
                      exclude_patterns: Optional[List[str]] = None,
                      progress_callback: Optional[Callable] = None) -> Dict[str, any]:
        """
        Download a model from HuggingFace or direct URL
        
        Args:
            model_id: HF model ID (e.g. "TheBloke/Llama-2-7B-GGUF") or direct URL
            revision: Git revision to download (branch, tag, commit hash)
            patterns: List of file patterns to include (e.g. ["*.gguf", "*.json"])
            exclude_patterns: List of file patterns to exclude
            progress_callback: Callback function for progress updates
            
        Returns:
            Dict with download results and model info
        """
        
        # Check if it's a direct URL
        if model_id.startswith(('http://', 'https://')):
            return self._download_from_url(model_id, progress_callback)
        else:
            return self._download_from_huggingface(
                model_id, revision, patterns, exclude_patterns, progress_callback
            )
    
    def _download_from_url(self, url: str, progress_callback: Optional[Callable] = None) -> Dict[str, any]:
        """Download a model from a direct URL"""
        
        try:
            # Parse filename from URL
            parsed = urlparse(url)
            filename = unquote(os.path.basename(parsed.path))
            if not filename:
                filename = "model.gguf"
            
            # Create download directory
            download_dir = self.cache_dir / "direct_downloads"
            download_dir.mkdir(exist_ok=True)
            
            file_path = download_dir / filename
            download_id = hashlib.md5(url.encode()).hexdigest()
            
            # Track download
            self.active_downloads[download_id] = {
                'url': url,
                'path': str(file_path),
                'status': 'downloading',
                'progress': 0
            }
            
            # Download with progress
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            block_size = 8192
            downloaded = 0
            
            with open(file_path, 'wb') as f:
                with tqdm(total=total_size, unit='B', unit_scale=True, desc=filename) as pbar:
                    for chunk in response.iter_content(block_size):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            pbar.update(len(chunk))
                            
                            # Update progress
                            progress = (downloaded / total_size * 100) if total_size > 0 else 0
                            self.active_downloads[download_id]['progress'] = progress
                            
                            if progress_callback:
                                progress_callback({
                                    'download_id': download_id,
                                    'filename': filename,
                                    'progress': progress,
                                    'downloaded': downloaded,
                                    'total': total_size
                                })
            
            # Mark as complete
            self.active_downloads[download_id]['status'] = 'completed'
            
            return {
                'success': True,
                'download_id': download_id,
                'files': [str(file_path)],
                'main_file': str(file_path),
                'size': os.path.getsize(file_path),
                'source': 'url'
            }
            
        except Exception as e:
            logger.error(f"Failed to download from URL {url}: {e}")
            if download_id in self.active_downloads:
                self.active_downloads[download_id]['status'] = 'failed'
                self.active_downloads[download_id]['error'] = str(e)
            return {
                'success': False,
                'error': str(e),
                'source': 'url'
            }
    
    def _download_from_huggingface(self,
                                  model_id: str,
                                  revision: Optional[str] = None,
                                  patterns: Optional[List[str]] = None,
                                  exclude_patterns: Optional[List[str]] = None,
                                  progress_callback: Optional[Callable] = None) -> Dict[str, any]:
        """Download a model from HuggingFace"""
        
        try:
            download_id = hashlib.md5(f"{model_id}:{revision}".encode()).hexdigest()
            
            # Track download
            self.active_downloads[download_id] = {
                'model_id': model_id,
                'revision': revision,
                'status': 'listing',
                'progress': 0
            }
            
            # List files in repo
            try:
                files = list_repo_files(model_id, revision=revision)
            except Exception as e:
                logger.error(f"Failed to list files for {model_id}: {e}")
                self.active_downloads[download_id]['status'] = 'failed'
                self.active_downloads[download_id]['error'] = str(e)
                return {
                    'success': False,
                    'error': f"Failed to list files: {str(e)}",
                    'source': 'huggingface'
                }
            
            # Filter files based on patterns
            files_to_download = self._filter_files(files, patterns, exclude_patterns)
            
            if not files_to_download:
                return {
                    'success': False,
                    'error': 'No files matched the specified patterns',
                    'source': 'huggingface'
                }
            
            # Update status
            self.active_downloads[download_id]['status'] = 'downloading'
            self.active_downloads[download_id]['total_files'] = len(files_to_download)
            
            # Download files
            downloaded_files = []
            model_dir = self.cache_dir / model_id.replace('/', '_')
            model_dir.mkdir(parents=True, exist_ok=True)
            
            for idx, filename in enumerate(files_to_download):
                try:
                    logger.info(f"Downloading {filename} from {model_id}")
                    
                    # Download file
                    local_path = hf_hub_download(
                        repo_id=model_id,
                        filename=filename,
                        revision=revision,
                        cache_dir=str(self.cache_dir),
                        local_dir=str(model_dir),
                        resume_download=True
                    )
                    
                    downloaded_files.append(local_path)
                    
                    # Update progress
                    progress = ((idx + 1) / len(files_to_download)) * 100
                    self.active_downloads[download_id]['progress'] = progress
                    self.active_downloads[download_id]['completed_files'] = idx + 1
                    
                    if progress_callback:
                        progress_callback({
                            'download_id': download_id,
                            'model_id': model_id,
                            'current_file': filename,
                            'progress': progress,
                            'completed': idx + 1,
                            'total': len(files_to_download)
                        })
                        
                except Exception as e:
                    logger.error(f"Failed to download {filename}: {e}")
                    # Continue with other files
            
            # Find main model file
            main_file = self._find_main_model_file(downloaded_files)
            
            # Mark as complete
            self.active_downloads[download_id]['status'] = 'completed'
            
            return {
                'success': True,
                'download_id': download_id,
                'model_id': model_id,
                'revision': revision,
                'files': downloaded_files,
                'main_file': main_file,
                'size': sum(os.path.getsize(f) for f in downloaded_files),
                'source': 'huggingface'
            }
            
        except Exception as e:
            logger.error(f"Failed to download {model_id}: {e}")
            if download_id in self.active_downloads:
                self.active_downloads[download_id]['status'] = 'failed'
                self.active_downloads[download_id]['error'] = str(e)
            return {
                'success': False,
                'error': str(e),
                'source': 'huggingface'
            }
    
    def _filter_files(self, files: List[str], patterns: Optional[List[str]], exclude_patterns: Optional[List[str]]) -> List[str]:
        """Filter files based on include/exclude patterns"""
        
        # Default patterns if none specified
        if not patterns:
            patterns = ["*.gguf", "*.json", "*.txt", "config.json", "tokenizer.json"]
        
        # Default excludes
        if not exclude_patterns:
            exclude_patterns = ["*.md", ".gitattributes", ".gitignore"]
        
        filtered = []
        for file in files:
            # Check if file matches any include pattern
            include = any(self._match_pattern(file, pattern) for pattern in patterns)
            
            # Check if file matches any exclude pattern
            exclude = any(self._match_pattern(file, pattern) for pattern in exclude_patterns)
            
            if include and not exclude:
                filtered.append(file)
        
        return filtered
    
    def _match_pattern(self, filename: str, pattern: str) -> bool:
        """Simple pattern matching (supports * wildcard)"""
        if '*' in pattern:
            import fnmatch
            return fnmatch.fnmatch(filename, pattern)
        return pattern in filename
    
    def _find_main_model_file(self, files: List[str]) -> Optional[str]:
        """Find the main model file from downloaded files"""
        
        # Look for GGUF files first
        gguf_files = [f for f in files if f.endswith('.gguf')]
        if gguf_files:
            # Prefer files with specific quantization indicators
            for quant in ['q4_k_m', 'q5_k_m', 'q4_0', 'q8_0']:
                for file in gguf_files:
                    if quant in file.lower():
                        return file
            # Return first GGUF file if no specific quantization found
            return gguf_files[0]
        
        # Look for other model formats
        for ext in ['.bin', '.safetensors', '.pt', '.pth']:
            model_files = [f for f in files if f.endswith(ext)]
            if model_files:
                return model_files[0]
        
        return None
    
    def list_downloaded_models(self) -> List[Dict[str, any]]:
        """List all downloaded models"""
        
        models = []
        
        # Check direct downloads
        direct_dir = self.cache_dir / "direct_downloads"
        if direct_dir.exists():
            for file in direct_dir.glob("*.gguf"):
                models.append({
                    'name': file.name,
                    'path': str(file),
                    'size': file.stat().st_size,
                    'modified': file.stat().st_mtime,
                    'source': 'direct'
                })
        
        # Check HF downloads
        for model_dir in self.cache_dir.iterdir():
            if model_dir.is_dir() and model_dir.name != "direct_downloads":
                # Look for model files
                model_files = list(model_dir.rglob("*.gguf")) + \
                             list(model_dir.rglob("*.bin")) + \
                             list(model_dir.rglob("*.safetensors"))
                
                for file in model_files:
                    models.append({
                        'name': model_dir.name.replace('_', '/'),
                        'path': str(file),
                        'size': file.stat().st_size,
                        'modified': file.stat().st_mtime,
                        'source': 'huggingface'
                    })
        
        return models
    
    def get_download_status(self, download_id: str) -> Optional[Dict[str, any]]:
        """Get status of a specific download"""
        return self.active_downloads.get(download_id)
    
    def get_all_downloads(self) -> Dict[str, Dict[str, any]]:
        """Get status of all downloads"""
        return self.active_downloads.copy()
    
    def cancel_download(self, download_id: str) -> bool:
        """Cancel an active download"""
        if download_id in self.active_downloads:
            self.active_downloads[download_id]['status'] = 'cancelled'
            return True
        return False
    
    def search_models(self, query: str, limit: int = 10) -> List[Dict[str, any]]:
        """Search for models on HuggingFace"""
        
        try:
            from huggingface_hub import list_models
            
            # Search for GGUF models
            models = list(list_models(
                search=query,
                filter="gguf",
                limit=limit
            ))
            
            results = []
            for model in models:
                results.append({
                    'id': model.id,
                    'author': model.author,
                    'name': model.modelId.split('/')[-1] if '/' in model.modelId else model.modelId,
                    'downloads': getattr(model, 'downloads', 0),
                    'likes': getattr(model, 'likes', 0),
                    'tags': model.tags,
                    'created': getattr(model, 'created_at', None)
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search models: {e}")
            return []
    
    def get_model_info(self, model_id: str) -> Optional[Dict[str, any]]:
        """Get information about a model from HuggingFace"""
        
        try:
            from huggingface_hub import model_info
            
            info = model_info(model_id)
            
            # Extract relevant information
            return {
                'id': info.id,
                'author': info.author,
                'name': info.modelId.split('/')[-1] if '/' in info.modelId else info.modelId,
                'downloads': getattr(info, 'downloads', 0),
                'likes': getattr(info, 'likes', 0),
                'tags': info.tags,
                'created': getattr(info, 'created_at', None),
                'last_modified': getattr(info, 'lastModified', None),
                'siblings': [{'name': s.rfilename, 'size': s.size} for s in info.siblings] if hasattr(info, 'siblings') else []
            }
            
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return None


def main():
    """Example usage of ModelDownloader"""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create downloader
    downloader = ModelDownloader()
    
    print("Model Downloader Demo")
    print("=" * 50)
    
    # Search for models
    print("\nSearching for Llama GGUF models...")
    results = downloader.search_models("llama gguf", limit=5)
    
    for model in results:
        print(f"- {model['id']} (downloads: {model['downloads']}, likes: {model['likes']})")
    
    # Example download
    if results:
        model_id = results[0]['id']
        print(f"\nDownloading {model_id}...")
        
        def progress_callback(info):
            if 'current_file' in info:
                print(f"  Downloading {info['current_file']}: {info['progress']:.1f}%")
        
        result = downloader.download_model(
            model_id,
            patterns=["*.gguf"],
            progress_callback=progress_callback
        )
        
        if result['success']:
            print(f"\nDownload complete!")
            print(f"Files: {result['files']}")
            print(f"Main file: {result['main_file']}")
            print(f"Total size: {result['size'] / (1024**3):.2f} GB")
        else:
            print(f"Download failed: {result['error']}")
    
    # List downloaded models
    print("\nDownloaded models:")
    models = downloader.list_downloaded_models()
    for model in models:
        print(f"- {model['name']} ({model['size'] / (1024**3):.2f} GB)")


if __name__ == "__main__":
    main()