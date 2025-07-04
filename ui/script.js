// Enhanced GerdsenAI MLX Model Manager - Interactive Functionality
// Demonstrates modern UI interactions and structured logging

class EnhancedLogger {
    constructor() {
        this.logs = [];
        this.logLevels = {
            DEBUG: { priority: 0, color: '#5AC8FA', icon: 'fas fa-bug' },
            INFO: { priority: 1, color: '#5AC8FA', icon: 'fas fa-info-circle' },
            SUCCESS: { priority: 2, color: '#34C759', icon: 'fas fa-check-circle' },
            WARN: { priority: 3, color: '#FF9500', icon: 'fas fa-exclamation-triangle' },
            ERROR: { priority: 4, color: '#FF3B30', icon: 'fas fa-times-circle' }
        };
        this.currentFilter = 'all';
        this.maxLogs = 1000;
    }

    log(level, message, context = {}) {
        const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
        const logEntry = {
            timestamp,
            level,
            message,
            context,
            id: Date.now() + Math.random()
        };

        this.logs.unshift(logEntry);
        
        // Keep only the most recent logs
        if (this.logs.length > this.maxLogs) {
            this.logs = this.logs.slice(0, this.maxLogs);
        }

        this.updateLogDisplay();
        
        // Also log to console for debugging
        console.log(`[${timestamp}] ${level}: ${message}`, context);
    }

    debug(message, context) { this.log('DEBUG', message, context); }
    info(message, context) { this.log('INFO', message, context); }
    success(message, context) { this.log('SUCCESS', message, context); }
    warn(message, context) { this.log('WARN', message, context); }
    error(message, context) { this.log('ERROR', message, context); }

    setFilter(level) {
        this.currentFilter = level;
        this.updateLogDisplay();
    }

    getFilteredLogs() {
        if (this.currentFilter === 'all') {
            return this.logs;
        }
        return this.logs.filter(log => log.level.toLowerCase() === this.currentFilter);
    }

    updateLogDisplay() {
        const container = document.querySelector('.logs-container');
        if (!container) return;

        const filteredLogs = this.getFilteredLogs();
        
        container.innerHTML = filteredLogs.map(log => `
            <div class="log-entry ${log.level.toLowerCase()}">
                <div class="log-timestamp">${log.timestamp}</div>
                <div class="log-level">${log.level}</div>
                <div class="log-message">${log.message}</div>
            </div>
        `).join('');
    }

    exportLogs() {
        const logs = this.getFilteredLogs();
        const exportData = {
            exportTime: new Date().toISOString(),
            filter: this.currentFilter,
            totalLogs: logs.length,
            logs: logs
        };
        
        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `gerdsen-ai-logs-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        this.info('Logs exported successfully', { exportedCount: logs.length });
    }

    clearLogs() {
        this.logs = [];
        this.updateLogDisplay();
        this.info('Log history cleared');
    }
}

class PerformanceMonitor {
    constructor(logger) {
        this.logger = logger;
        this.metrics = {
            tokensPerSecond: [],
            memoryUsage: [],
            temperature: [],
            latency: [],
            cpuUsage: [],
            gpuUsage: [],
            neuralEngineUsage: []
        };
        this.isMonitoring = false;
        this.monitoringInterval = null;
    }

    start() {
        if (this.isMonitoring) return;
        
        this.isMonitoring = true;
        this.logger.info('Performance monitoring started');
        
        this.monitoringInterval = setInterval(() => {
            this.collectMetrics();
            this.updateUI();
        }, 1000);
    }

    stop() {
        if (!this.isMonitoring) return;
        
        this.isMonitoring = false;
        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
            this.monitoringInterval = null;
        }
        this.logger.info('Performance monitoring stopped');
    }

    collectMetrics() {
        // Simulate realistic performance metrics
        const now = Date.now();
        
        // Simulate tokens per second with some variance
        const baseTokens = 45.2;
        const tokensPerSecond = baseTokens + (Math.random() - 0.5) * 10;
        
        // Simulate memory usage (in GB)
        const baseMemory = 22.1;
        const memoryUsage = baseMemory + (Math.random() - 0.5) * 2;
        
        // Simulate temperature (in Celsius)
        const baseTemp = 68;
        const temperature = baseTemp + (Math.random() - 0.5) * 8;
        
        // Simulate latency (in ms)
        const baseLatency = 1.2;
        const latency = baseLatency + (Math.random() - 0.5) * 0.8;
        
        // Simulate resource usage percentages
        const cpuUsage = 34 + (Math.random() - 0.5) * 20;
        const gpuUsage = 78 + (Math.random() - 0.5) * 15;
        const neuralEngineUsage = 56 + (Math.random() - 0.5) * 25;

        // Store metrics (keep last 60 data points for 1-minute window)
        this.addMetric('tokensPerSecond', { time: now, value: tokensPerSecond });
        this.addMetric('memoryUsage', { time: now, value: memoryUsage });
        this.addMetric('temperature', { time: now, value: temperature });
        this.addMetric('latency', { time: now, value: latency });
        this.addMetric('cpuUsage', { time: now, value: cpuUsage });
        this.addMetric('gpuUsage', { time: now, value: gpuUsage });
        this.addMetric('neuralEngineUsage', { time: now, value: neuralEngineUsage });

        // Log performance warnings
        if (temperature > 75) {
            this.logger.warn(`High temperature detected: ${temperature.toFixed(1)}°C`, { temperature });
        }
        if (memoryUsage > 45) {
            this.logger.warn(`High memory usage: ${memoryUsage.toFixed(1)}GB`, { memoryUsage });
        }
        if (tokensPerSecond < 30) {
            this.logger.warn(`Low performance: ${tokensPerSecond.toFixed(1)} tokens/sec`, { tokensPerSecond });
        }
    }

    addMetric(type, dataPoint) {
        this.metrics[type].push(dataPoint);
        // Keep only last 60 data points (1 minute at 1-second intervals)
        if (this.metrics[type].length > 60) {
            this.metrics[type] = this.metrics[type].slice(-60);
        }
    }

    updateUI() {
        const latest = this.getLatestMetrics();
        
        // Update stat cards
        this.updateStatCard('tokens', latest.tokensPerSecond, 'Tokens/sec');
        this.updateStatCard('memory', latest.memoryUsage, 'GB');
        this.updateStatCard('temperature', latest.temperature, '°C');
        this.updateStatCard('latency', latest.latency, 'ms');
        
        // Update resource bars
        this.updateResourceBar('CPU Usage', latest.cpuUsage);
        this.updateResourceBar('GPU Usage', latest.gpuUsage);
        this.updateResourceBar('Memory', (latest.memoryUsage / 512) * 100); // Assuming 512GB total
        this.updateResourceBar('Neural Engine', latest.neuralEngineUsage);
    }

    updateStatCard(type, value, unit) {
        const cards = document.querySelectorAll('.stat-card');
        cards.forEach(card => {
            const content = card.querySelector('.stat-content h3');
            const label = card.querySelector('.stat-content p');
            if (label && label.textContent.includes(unit)) {
                content.textContent = value.toFixed(1);
            }
        });
    }

    updateResourceBar(label, percentage) {
        const bars = document.querySelectorAll('.resource-bar');
        bars.forEach(bar => {
            const labelElement = bar.querySelector('.resource-label span');
            if (labelElement && labelElement.textContent === label) {
                const valueElement = bar.querySelector('.resource-label span:last-child');
                const fillElement = bar.querySelector('.progress-fill');
                if (valueElement && fillElement) {
                    valueElement.textContent = `${Math.round(percentage)}%`;
                    fillElement.style.width = `${Math.min(100, Math.max(0, percentage))}%`;
                }
            }
        });
    }

    getLatestMetrics() {
        const latest = {};
        Object.keys(this.metrics).forEach(key => {
            const data = this.metrics[key];
            latest[key] = data.length > 0 ? data[data.length - 1].value : 0;
        });
        return latest;
    }
}

class ModelManager {
    constructor(logger) {
        this.logger = logger;
        this.activeModel = null;
        this.models = [
            {
                id: 'qwen-32b',
                name: 'Qwen2.5-Coder-32B-Instruct-4bit',
                description: 'High-performance code generation model optimized for development workflows',
                size: 22.2,
                speed: 45.2,
                quality: 95,
                status: 'running'
            },
            {
                id: 'deepseek-lite',
                name: 'DeepSeek-Coder-V2-Lite-Instruct-4bit',
                description: 'Lightweight coding assistant with excellent performance',
                size: 8.2,
                speed: 67.8,
                quality: 92,
                status: 'cached'
            },
            {
                id: 'llama-70b',
                name: 'Llama-3.3-70B-Instruct-4bit',
                description: 'Large general-purpose model for complex reasoning tasks',
                size: 47.0,
                speed: 28.5,
                quality: 98,
                status: 'available'
            }
        ];
    }

    loadModel(modelId) {
        const model = this.models.find(m => m.id === modelId);
        if (!model) {
            this.logger.error(`Model not found: ${modelId}`);
            return;
        }

        this.logger.info(`Loading model: ${model.name}`, { modelId, size: model.size });
        
        // Simulate loading time
        setTimeout(() => {
            if (this.activeModel) {
                this.activeModel.status = 'cached';
            }
            
            model.status = 'running';
            this.activeModel = model;
            
            this.logger.success(`Model loaded successfully: ${model.name}`, { 
                modelId, 
                loadTime: '2.3s',
                memoryUsage: `${model.size}GB`
            });
            
            this.updateModelUI();
        }, 2300);
    }

    stopModel(modelId) {
        const model = this.models.find(m => m.id === modelId);
        if (!model) return;

        model.status = 'cached';
        if (this.activeModel && this.activeModel.id === modelId) {
            this.activeModel = null;
        }

        this.logger.info(`Model stopped: ${model.name}`, { modelId });
        this.updateModelUI();
    }

    updateModelUI() {
        // Update active model card
        const activeModelCard = document.querySelector('.active-model-card');
        if (activeModelCard && this.activeModel) {
            const nameElement = activeModelCard.querySelector('.model-details h3');
            const descElement = activeModelCard.querySelector('.model-details p');
            if (nameElement) nameElement.textContent = this.activeModel.name;
            if (descElement) descElement.textContent = this.activeModel.description;
        }

        // Update model cards in models tab
        this.updateModelCards();
    }

    updateModelCards() {
        const modelsGrid = document.querySelector('.models-grid');
        if (!modelsGrid) return;

        modelsGrid.innerHTML = this.models.map(model => `
            <div class="model-card ${model.status === 'running' ? 'active' : ''}">
                <div class="model-card-header">
                    <div class="model-status-indicator ${model.status}"></div>
                    <h3>${model.name}</h3>
                </div>
                <div class="model-card-content">
                    <p>${model.description}</p>
                    <div class="model-metrics">
                        <div class="metric">
                            <span class="metric-label">Size:</span>
                            <span class="metric-value">${model.size}GB</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Speed:</span>
                            <span class="metric-value">${model.speed} tok/s</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Quality:</span>
                            <span class="metric-value">${model.quality}%</span>
                        </div>
                    </div>
                </div>
                <div class="model-card-actions">
                    ${this.getModelActions(model)}
                </div>
            </div>
        `).join('');

        // Add event listeners to new buttons
        this.attachModelEventListeners();
    }

    getModelActions(model) {
        switch (model.status) {
            case 'running':
                return `
                    <button class="btn btn-sm btn-secondary" onclick="app.modelManager.configureModel('${model.id}')">Configure</button>
                    <button class="btn btn-sm btn-danger" onclick="app.modelManager.stopModel('${model.id}')">Stop</button>
                `;
            case 'cached':
                return `
                    <button class="btn btn-sm btn-primary" onclick="app.modelManager.loadModel('${model.id}')">Load</button>
                    <button class="btn btn-sm btn-secondary" onclick="app.modelManager.configureModel('${model.id}')">Configure</button>
                `;
            case 'available':
                return `
                    <button class="btn btn-sm btn-primary" onclick="app.modelManager.downloadModel('${model.id}')">Download</button>
                    <button class="btn btn-sm btn-secondary" onclick="app.modelManager.showModelInfo('${model.id}')">Info</button>
                `;
            default:
                return '';
        }
    }

    attachModelEventListeners() {
        // Event listeners are handled via onclick attributes for simplicity in this prototype
    }

    configureModel(modelId) {
        this.logger.info(`Opening configuration for model: ${modelId}`);
        // In a real implementation, this would open a configuration modal
    }

    downloadModel(modelId) {
        const model = this.models.find(m => m.id === modelId);
        if (!model) return;

        this.logger.info(`Starting download: ${model.name}`, { modelId, size: model.size });
        
        // Simulate download progress
        let progress = 0;
        const downloadInterval = setInterval(() => {
            progress += Math.random() * 10;
            if (progress >= 100) {
                progress = 100;
                clearInterval(downloadInterval);
                model.status = 'cached';
                this.logger.success(`Download completed: ${model.name}`, { modelId });
                this.updateModelCards();
            } else {
                this.logger.info(`Download progress: ${Math.round(progress)}%`, { modelId, progress });
            }
        }, 500);
    }

    showModelInfo(modelId) {
        const model = this.models.find(m => m.id === modelId);
        if (!model) return;

        this.logger.info(`Showing info for model: ${model.name}`, { modelId });
        // In a real implementation, this would show detailed model information
    }
}

class UIManager {
    constructor(logger) {
        this.logger = logger;
        this.currentTab = 'dashboard';
        this.init();
    }

    init() {
        this.setupTabNavigation();
        this.setupLogControls();
        this.setupSettingsButton();
        this.logger.info('UI Manager initialized');
    }

    setupTabNavigation() {
        const navItems = document.querySelectorAll('.nav-item');
        const tabContents = document.querySelectorAll('.tab-content');

        navItems.forEach(item => {
            item.addEventListener('click', () => {
                const tabId = item.getAttribute('data-tab');
                this.switchTab(tabId);
            });
        });
    }

    switchTab(tabId) {
        if (this.currentTab === tabId) return;

        this.logger.debug(`Switching to tab: ${tabId}`, { previousTab: this.currentTab });

        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
            if (item.getAttribute('data-tab') === tabId) {
                item.classList.add('active');
            }
        });

        // Update content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
            if (content.id === tabId) {
                content.classList.add('active');
            }
        });

        this.currentTab = tabId;
        this.logger.info(`Switched to ${tabId} tab`);
    }

    setupLogControls() {
        const logLevelSelect = document.getElementById('logLevel');
        if (logLevelSelect) {
            logLevelSelect.addEventListener('change', (e) => {
                app.logger.setFilter(e.target.value);
                this.logger.debug(`Log filter changed to: ${e.target.value}`);
            });
        }

        // Export logs button
        const exportBtn = document.querySelector('.logs-controls .btn:nth-child(2)');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => {
                app.logger.exportLogs();
            });
        }

        // Clear logs button
        const clearBtn = document.querySelector('.logs-controls .btn:nth-child(3)');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                if (confirm('Are you sure you want to clear all logs?')) {
                    app.logger.clearLogs();
                }
            });
        }
    }

    setupSettingsButton() {
        const settingsBtn = document.getElementById('settingsBtn');
        if (settingsBtn) {
            settingsBtn.addEventListener('click', () => {
                this.logger.info('Settings button clicked');
                // In a real implementation, this would open settings modal
            });
        }
    }

    showNotification(message, type = 'info', duration = 3000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        // Style the notification
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            padding: '12px 16px',
            borderRadius: '8px',
            color: 'white',
            fontWeight: '500',
            zIndex: '1000',
            transform: 'translateX(100%)',
            transition: 'transform 0.3s ease-out',
            maxWidth: '300px'
        });

        // Set background color based on type
        const colors = {
            info: '#5AC8FA',
            success: '#34C759',
            warning: '#FF9500',
            error: '#FF3B30'
        };
        notification.style.backgroundColor = colors[type] || colors.info;

        document.body.appendChild(notification);

        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 10);

        // Animate out and remove
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, duration);
    }
}

// Main Application Class
class GerdsenAIApp {
    constructor() {
        this.logger = new EnhancedLogger();
        this.performanceMonitor = new PerformanceMonitor(this.logger);
        this.modelManager = new ModelManager(this.logger);
        this.uiManager = new UIManager(this.logger);
        
        this.init();
    }

    init() {
        this.logger.info('GerdsenAI MLX Model Manager starting up');
        this.logger.success('Enhanced architecture loaded successfully');
        
        // Initialize components
        this.performanceMonitor.start();
        this.modelManager.updateModelUI();
        
        // Simulate initial system optimization
        setTimeout(() => {
            this.logger.success('GPU memory wiring configured: 410GB allocated');
            this.logger.info('Metal Performance Shaders enabled');
            this.logger.info('Neural Engine acceleration activated');
            this.logger.success('System optimization complete');
        }, 1000);

        // Simulate model loading
        setTimeout(() => {
            this.logger.info('Loading default model: Qwen2.5-Coder-32B-Instruct-4bit');
            this.modelManager.activeModel = this.modelManager.models[0];
            this.logger.success('Model loaded and ready for inference');
        }, 2000);

        this.logger.info('Application initialization complete');
    }

    shutdown() {
        this.logger.info('Shutting down GerdsenAI MLX Model Manager');
        this.performanceMonitor.stop();
        this.logger.success('Shutdown complete');
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new GerdsenAIApp();
    
    // Add some demo interactions
    setTimeout(() => {
        app.uiManager.showNotification('Welcome to the enhanced GerdsenAI interface!', 'success');
    }, 3000);
});

// Handle page unload
window.addEventListener('beforeunload', () => {
    if (window.app) {
        window.app.shutdown();
    }
});

// Export for global access
window.GerdsenAIApp = GerdsenAIApp;


// Model Drag-and-Drop Handler
class ModelDragDropHandler {
    constructor(logger) {
        this.logger = logger;
        this.dropZone = null;
        this.dropOverlay = null;
        this.fileInput = null;
        this.supportedFormats = ['.mlx', '.gguf', '.safetensors', '.bin', '.pt', '.pth'];
    }

    init() {
        this.dropZone = document.getElementById('modelDropZone');
        this.dropOverlay = document.getElementById('dropOverlay');
        this.fileInput = document.getElementById('fileInput');
        
        if (!this.dropZone) return;

        // Drag and drop events
        this.dropZone.addEventListener('dragover', this.handleDragOver.bind(this));
        this.dropZone.addEventListener('dragenter', this.handleDragEnter.bind(this));
        this.dropZone.addEventListener('dragleave', this.handleDragLeave.bind(this));
        this.dropZone.addEventListener('drop', this.handleDrop.bind(this));
        
        // File input change
        if (this.fileInput) {
            this.fileInput.addEventListener('change', this.handleFileSelect.bind(this));
        }

        this.logger.info('Model drag-and-drop handler initialized');
    }

    handleDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'copy';
    }

    handleDragEnter(e) {
        e.preventDefault();
        this.dropZone.classList.add('drag-over');
        if (this.dropOverlay) {
            this.dropOverlay.style.display = 'flex';
        }
    }

    handleDragLeave(e) {
        e.preventDefault();
        if (!this.dropZone.contains(e.relatedTarget)) {
            this.dropZone.classList.remove('drag-over');
            if (this.dropOverlay) {
                this.dropOverlay.style.display = 'none';
            }
        }
    }

    handleDrop(e) {
        e.preventDefault();
        this.dropZone.classList.remove('drag-over');
        if (this.dropOverlay) {
            this.dropOverlay.style.display = 'none';
        }
        
        const files = Array.from(e.dataTransfer.files);
        this.processFiles(files);
    }

    handleFileSelect(e) {
        const files = Array.from(e.target.files);
        this.processFiles(files);
    }

    processFiles(files) {
        const validFiles = files.filter(file => {
            const extension = '.' + file.name.split('.').pop().toLowerCase();
            return this.supportedFormats.includes(extension);
        });

        if (validFiles.length === 0) {
            this.logger.warn('No supported model files found in selection', { 
                totalFiles: files.length,
                supportedFormats: this.supportedFormats 
            });
            app.uiManager.showNotification('No supported model files found', 'warning');
            return;
        }

        this.logger.info(`Processing ${validFiles.length} model files`, { 
            validFiles: validFiles.length,
            totalFiles: files.length 
        });

        validFiles.forEach(file => {
            this.addModelFile(file);
        });
    }

    addModelFile(file) {
        this.logger.info(`Adding model file: ${file.name}`, { 
            size: this.formatFileSize(file.size),
            type: file.type || 'unknown',
            lastModified: new Date(file.lastModified).toISOString()
        });

        // Simulate model processing
        app.uiManager.showNotification(`Processing ${file.name}...`, 'info');
        
        // Simulate validation and optimization
        setTimeout(() => {
            this.logger.success(`Model file validated: ${file.name}`, {
                status: 'validated',
                format: 'compatible'
            });
        }, 1000);

        setTimeout(() => {
            this.logger.info(`Optimizing model: ${file.name}`, {
                optimization: 'quantization',
                targetFormat: 'MLX'
            });
        }, 1500);
        
        setTimeout(() => {
            this.logger.success(`Model file processed: ${file.name}`, {
                status: 'ready',
                optimized: true,
                memoryFootprint: this.estimateMemoryFootprint(file.size)
            });
            app.uiManager.showNotification(`${file.name} added successfully!`, 'success');
            
            // Add to model list
            this.addToModelList(file);
        }, 3000);
    }

    addToModelList(file) {
        const modelId = 'custom-' + Date.now();
        const modelName = file.name.replace(/\.[^/.]+$/, ""); // Remove extension
        
        const newModel = {
            id: modelId,
            name: modelName,
            description: 'Custom model added via drag-and-drop',
            size: file.size / (1024 * 1024 * 1024), // Convert to GB
            speed: 35.0 + Math.random() * 20, // Estimated speed
            quality: 85 + Math.random() * 10, // Estimated quality
            status: 'cached'
        };

        app.modelManager.models.push(newModel);
        app.modelManager.updateModelCards();
        
        this.logger.info(`Model added to library: ${modelName}`, { 
            modelId,
            estimatedPerformance: {
                speed: newModel.speed.toFixed(1) + ' tok/s',
                quality: newModel.quality.toFixed(0) + '%'
            }
        });
    }

    estimateMemoryFootprint(fileSize) {
        // Rough estimation based on file size
        const sizeGB = fileSize / (1024 * 1024 * 1024);
        return `~${sizeGB.toFixed(1)}GB`;
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

// Update the main application class to include drag-drop handler
const originalGerdsenAIAppInit = GerdsenAIApp.prototype.init;
GerdsenAIApp.prototype.init = function() {
    originalGerdsenAIAppInit.call(this);
    
    // Initialize drag-drop handler
    this.dragDropHandler = new ModelDragDropHandler(this.logger);
    
    // Initialize drag-drop when switching to models tab
    const originalSwitchTab = this.uiManager.switchTab;
    this.uiManager.switchTab = function(tabId) {
        originalSwitchTab.call(this, tabId);
        if (tabId === 'models') {
            setTimeout(() => {
                app.dragDropHandler.init();
            }, 100);
        }
    };
};

