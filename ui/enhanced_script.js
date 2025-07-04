/**
 * Enhanced GerdsenAI MLX Manager - Dynamic UI Controller
 * Integrates with Apple Silicon detector and MLX manager for real-time data
 */

class GerdsenAIManager {
    constructor() {
        this.wsConnection = null;
        this.charts = {};
        this.updateIntervals = {};
        this.currentTab = 'dashboard';
        this.systemData = {
            hardware: {},
            performance: {},
            models: [],
            optimization: {}
        };
        
        this.init();
    }

    async init() {
        this.setupEventListeners();
        this.setupWebSocket();
        this.setupCharts();
        this.startDataUpdates();
        this.detectSystemCapabilities();
        
        // Show loading overlay initially
        this.showLoading('Initializing GerdsenAI...');
        
        // Hide loading after initialization
        setTimeout(() => {
            this.hideLoading();
            this.showNotification('success', 'System Ready', 'GerdsenAI MLX Manager is ready for use');
        }, 2000);
    }

    setupEventListeners() {
        // Tab navigation
        document.querySelectorAll('.tab-item').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const tabId = e.currentTarget.dataset.tab;
                this.switchTab(tabId);
            });
        });

        // Window controls
        document.querySelector('.traffic-light.minimize')?.addEventListener('click', () => {
            this.minimizeToTray();
        });

        // Model drop zone
        const dropZone = document.getElementById('modelDropZone');
        if (dropZone) {
            this.setupModelDropZone(dropZone);
        }

        // Optimization controls
        this.setupOptimizationControls();

        // Performance controls
        this.setupPerformanceControls();

        // Search functionality
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.handleSearch(e.target.value);
            });
        }
    }

    setupWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.wsConnection = new WebSocket(wsUrl);
        
        this.wsConnection.onopen = () => {
            console.log('WebSocket connected');
            this.updateConnectionStatus(true);
        };
        
        this.wsConnection.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };
        
        this.wsConnection.onclose = () => {
            console.log('WebSocket disconnected');
            this.updateConnectionStatus(false);
            // Attempt to reconnect after 5 seconds
            setTimeout(() => this.setupWebSocket(), 5000);
        };
        
        this.wsConnection.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.showNotification('error', 'Connection Error', 'Failed to connect to server');
        };
    }

    setupCharts() {
        // Real-time monitoring chart
        const realtimeCtx = document.getElementById('realtimeChart');
        if (realtimeCtx) {
            this.charts.realtime = new Chart(realtimeCtx, {
                type: 'line',
                data: {
                    labels: Array.from({length: 60}, (_, i) => i),
                    datasets: [{
                        label: 'CPU Frequency',
                        data: Array.from({length: 60}, () => Math.random() * 100),
                        borderColor: '#007aff',
                        backgroundColor: 'rgba(0, 122, 255, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        x: {
                            display: false
                        },
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: 'rgba(84, 84, 88, 0.3)'
                            },
                            ticks: {
                                color: '#98989d'
                            }
                        }
                    },
                    elements: {
                        point: {
                            radius: 0
                        }
                    }
                }
            });
        }

        // Memory usage chart
        const memoryCtx = document.getElementById('memoryChart');
        if (memoryCtx) {
            this.charts.memory = new Chart(memoryCtx, {
                type: 'line',
                data: {
                    labels: Array.from({length: 30}, (_, i) => i),
                    datasets: [{
                        label: 'Memory Usage',
                        data: Array.from({length: 30}, () => Math.random() * 100),
                        borderColor: '#30d158',
                        backgroundColor: 'rgba(48, 209, 88, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        x: {
                            display: false
                        },
                        y: {
                            beginAtZero: true,
                            max: 100,
                            grid: {
                                color: 'rgba(84, 84, 88, 0.3)'
                            },
                            ticks: {
                                color: '#98989d'
                            }
                        }
                    },
                    elements: {
                        point: {
                            radius: 0
                        }
                    }
                }
            });
        }

        // Performance trends chart
        const performanceCtx = document.getElementById('performanceChart');
        if (performanceCtx) {
            this.charts.performance = new Chart(performanceCtx, {
                type: 'line',
                data: {
                    labels: Array.from({length: 24}, (_, i) => `${i}:00`),
                    datasets: [
                        {
                            label: 'CPU Usage',
                            data: Array.from({length: 24}, () => Math.random() * 100),
                            borderColor: '#007aff',
                            backgroundColor: 'rgba(0, 122, 255, 0.1)',
                            tension: 0.4
                        },
                        {
                            label: 'Memory Usage',
                            data: Array.from({length: 24}, () => Math.random() * 100),
                            borderColor: '#30d158',
                            backgroundColor: 'rgba(48, 209, 88, 0.1)',
                            tension: 0.4
                        },
                        {
                            label: 'Temperature',
                            data: Array.from({length: 24}, () => 40 + Math.random() * 30),
                            borderColor: '#ff9500',
                            backgroundColor: 'rgba(255, 149, 0, 0.1)',
                            tension: 0.4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: {
                                color: '#98989d',
                                usePointStyle: true
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: {
                                color: 'rgba(84, 84, 88, 0.3)'
                            },
                            ticks: {
                                color: '#98989d'
                            }
                        },
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: 'rgba(84, 84, 88, 0.3)'
                            },
                            ticks: {
                                color: '#98989d'
                            }
                        }
                    }
                }
            });
        }
    }

    startDataUpdates() {
        // Update system metrics every 2 seconds
        this.updateIntervals.metrics = setInterval(() => {
            this.updateSystemMetrics();
        }, 2000);

        // Update hardware info every 5 seconds
        this.updateIntervals.hardware = setInterval(() => {
            this.updateHardwareInfo();
        }, 5000);

        // Update performance data every 10 seconds
        this.updateIntervals.performance = setInterval(() => {
            this.updatePerformanceData();
        }, 10000);

        // Update charts every 3 seconds
        this.updateIntervals.charts = setInterval(() => {
            this.updateCharts();
        }, 3000);
    }

    async detectSystemCapabilities() {
        try {
            const response = await fetch('/api/hardware/detect');
            const data = await response.json();
            
            this.systemData.hardware = data;
            this.updateHardwareDisplay(data);
            this.updateHeaderHardwareInfo(data);
            
        } catch (error) {
            console.error('Failed to detect system capabilities:', error);
            this.showNotification('error', 'Detection Failed', 'Could not detect system capabilities');
        }
    }

    async updateSystemMetrics() {
        try {
            const response = await fetch('/api/hardware/metrics');
            const data = await response.json();
            
            // Update metric cards
            this.updateElement('cpuUsage', `${data.cpu_usage?.toFixed(1) || '--'}%`);
            this.updateElement('memoryUsage', `${data.memory_used?.toFixed(1) || '--'} GB`);
            this.updateElement('temperature', `${data.temperature?.toFixed(0) || '--'}°C`);
            this.updateElement('loadedModels', data.loaded_models || 0);
            
            // Update memory progress bar
            const memoryProgress = document.getElementById('memoryProgress');
            const memoryText = document.getElementById('memoryText');
            if (memoryProgress && data.memory_used && data.memory_total) {
                const percentage = (data.memory_used / data.memory_total) * 100;
                memoryProgress.style.width = `${percentage}%`;
                memoryText.textContent = `${data.memory_used.toFixed(1)} GB / ${data.memory_total.toFixed(1)} GB`;
            }
            
            // Update CPU cores
            if (data.cpu_cores) {
                this.updateCPUCores(data.cpu_cores);
            }
            
        } catch (error) {
            console.error('Failed to update system metrics:', error);
        }
    }

    async updateHardwareInfo() {
        try {
            const response = await fetch('/api/hardware/info');
            const data = await response.json();
            
            this.systemData.hardware = { ...this.systemData.hardware, ...data };
            this.updateHardwareDisplay(data);
            
        } catch (error) {
            console.error('Failed to update hardware info:', error);
        }
    }

    async updatePerformanceData() {
        try {
            const response = await fetch('/api/performance/metrics');
            const data = await response.json();
            
            this.systemData.performance = data;
            this.updatePerformanceDisplay(data);
            
        } catch (error) {
            console.error('Failed to update performance data:', error);
        }
    }

    updateCharts() {
        // Update real-time chart
        if (this.charts.realtime) {
            const newData = Math.random() * 100;
            this.charts.realtime.data.datasets[0].data.shift();
            this.charts.realtime.data.datasets[0].data.push(newData);
            this.charts.realtime.update('none');
        }

        // Update memory chart
        if (this.charts.memory) {
            const newData = Math.random() * 100;
            this.charts.memory.data.datasets[0].data.shift();
            this.charts.memory.data.datasets[0].data.push(newData);
            this.charts.memory.update('none');
        }
    }

    updateHardwareDisplay(data) {
        // Update chip information
        if (data.chip_name) {
            this.updateElement('chipName', data.chip_name);
            this.updateElement('chipVariant', data.chip_variant || '');
        }
        
        // Update specifications
        if (data.cpu_cores) {
            this.updateElement('cpuCores', `${data.cpu_cores.performance || 0} P + ${data.cpu_cores.efficiency || 0} E`);
        }
        
        if (data.gpu_cores) {
            this.updateElement('gpuCores', `${data.gpu_cores} cores`);
        }
        
        if (data.neural_engine) {
            this.updateElement('neuralEngineCores', `${data.neural_engine.cores || 16} cores`);
        }
        
        if (data.memory) {
            this.updateElement('unifiedMemory', `${data.memory.total || '--'} GB Unified`);
            this.updateElement('memoryBandwidth', `${data.memory.bandwidth || '--'} GB/s`);
        }
        
        if (data.process_node) {
            this.updateElement('processNode', data.process_node);
        }
        
        // Update framework capabilities
        this.updateFrameworkCapabilities(data.frameworks || {});
    }

    updateHeaderHardwareInfo(data) {
        const hardwareInfo = document.getElementById('hardwareInfo');
        if (hardwareInfo && data.chip_name && data.memory) {
            const chipText = `${data.chip_name} • ${data.memory.total || '--'} GB`;
            hardwareInfo.querySelector('span').textContent = chipText;
        }
    }

    updateCPUCores(coresData) {
        const coresGrid = document.getElementById('cpuCoresGrid');
        if (!coresGrid) return;
        
        coresGrid.innerHTML = '';
        
        // Performance cores
        for (let i = 0; i < (coresData.performance || 0); i++) {
            const coreElement = this.createCoreElement(i, 'performance', coresData.performance_usage?.[i] || 0);
            coresGrid.appendChild(coreElement);
        }
        
        // Efficiency cores
        for (let i = 0; i < (coresData.efficiency || 0); i++) {
            const coreElement = this.createCoreElement(i, 'efficiency', coresData.efficiency_usage?.[i] || 0);
            coresGrid.appendChild(coreElement);
        }
    }

    createCoreElement(index, type, usage) {
        const core = document.createElement('div');
        core.className = `cpu-core ${type}`;
        core.style.setProperty('--usage', `${usage}%`);
        
        core.innerHTML = `
            <div class="core-label">${type === 'performance' ? 'P' : 'E'}${index}</div>
            <div class="core-usage">${usage.toFixed(0)}%</div>
        `;
        
        // Update the height of the usage indicator
        core.style.setProperty('--usage-height', `${usage}%`);
        
        return core;
    }

    updateFrameworkCapabilities(frameworks) {
        const frameworkItems = {
            'coremlFramework': frameworks.coreml || {},
            'mlxFramework': frameworks.mlx || {},
            'metalFramework': frameworks.metal || {}
        };
        
        Object.entries(frameworkItems).forEach(([elementId, framework]) => {
            const element = document.getElementById(elementId);
            if (element) {
                const statusElement = element.querySelector('.framework-status');
                const versionElement = element.querySelector('.framework-version');
                
                if (statusElement) {
                    statusElement.textContent = framework.available ? 'Available' : 'Not Available';
                    statusElement.style.color = framework.available ? '#30d158' : '#ff453a';
                }
                
                if (versionElement && framework.version) {
                    versionElement.textContent = framework.version;
                }
            }
        });
    }

    updatePerformanceDisplay(data) {
        // Update performance metrics
        if (data.overall_score) {
            this.updateElement('overallScore', `${data.overall_score.toFixed(0)}%`);
            this.updateProgressBar('overallProgress', data.overall_score);
        }
        
        if (data.cpu_efficiency) {
            this.updateElement('cpuEfficiency', `${data.cpu_efficiency.toFixed(0)}%`);
            this.updateProgressBar('cpuProgress', data.cpu_efficiency);
        }
        
        if (data.memory_efficiency) {
            this.updateElement('memoryEfficiency', `${data.memory_efficiency.toFixed(0)}%`);
            this.updateProgressBar('memoryProgress', data.memory_efficiency);
        }
        
        if (data.thermal_efficiency) {
            this.updateElement('thermalEfficiency', `${data.thermal_efficiency.toFixed(0)}%`);
            this.updateProgressBar('thermalProgress', data.thermal_efficiency);
        }
        
        // Update recommendations
        if (data.recommendations) {
            this.updateRecommendations(data.recommendations);
        }
    }

    updateRecommendations(recommendations) {
        const recommendationsList = document.getElementById('recommendationsList');
        if (!recommendationsList) return;
        
        recommendationsList.innerHTML = '';
        
        recommendations.forEach(rec => {
            const item = document.createElement('div');
            item.className = `recommendation-item ${rec.priority}-priority`;
            item.innerHTML = `
                <div class="recommendation-title">${rec.title}</div>
                <div class="recommendation-description">${rec.description}</div>
            `;
            recommendationsList.appendChild(item);
        });
    }

    setupModelDropZone(dropZone) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, this.preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => dropZone.classList.add('drag-over'), false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => dropZone.classList.remove('drag-over'), false);
        });

        dropZone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            this.handleModelFiles(files);
        }, false);

        // File input change
        const fileInput = document.getElementById('fileInput');
        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                this.handleModelFiles(e.target.files);
            });
        }
    }

    setupOptimizationControls() {
        // Auto optimization toggle
        const autoOptToggle = document.getElementById('autoOptimization');
        if (autoOptToggle) {
            autoOptToggle.addEventListener('change', (e) => {
                this.toggleAutoOptimization(e.target.checked);
            });
        }

        // Individual setting toggles
        const settings = ['thermalManagement', 'powerManagement', 'neuralEnginePriority', 'metalAcceleration'];
        settings.forEach(settingId => {
            const toggle = document.getElementById(settingId);
            if (toggle) {
                toggle.addEventListener('change', (e) => {
                    this.updateOptimizationSetting(settingId, e.target.checked);
                });
            }
        });

        // Action buttons
        const actions = {
            'optimizeAllModels': () => this.optimizeAllModels(),
            'clearModelCache': () => this.clearModelCache(),
            'benchmarkSystem': () => this.benchmarkSystem(),
            'exportSettings': () => this.exportSettings()
        };

        Object.entries(actions).forEach(([buttonId, action]) => {
            const button = document.getElementById(buttonId);
            if (button) {
                button.addEventListener('click', action);
            }
        });
    }

    setupPerformanceControls() {
        // Time range selector
        const timeRangeSelect = document.getElementById('performanceTimeRange');
        if (timeRangeSelect) {
            timeRangeSelect.addEventListener('change', (e) => {
                this.updatePerformanceTimeRange(e.target.value);
            });
        }

        // Chart metric selector
        const chartMetricSelect = document.getElementById('chartMetric');
        if (chartMetricSelect) {
            chartMetricSelect.addEventListener('change', (e) => {
                this.updateChartMetric(e.target.value);
            });
        }

        // Monitoring metric selector
        const monitoringMetricSelect = document.getElementById('monitoringMetric');
        if (monitoringMetricSelect) {
            monitoringMetricSelect.addEventListener('change', (e) => {
                this.updateMonitoringMetric(e.target.value);
            });
        }

        // Refresh recommendations button
        const refreshBtn = document.getElementById('refreshRecommendations');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshRecommendations();
            });
        }
    }

    switchTab(tabId) {
        // Update tab navigation
        document.querySelectorAll('.tab-item').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabId}"]`).classList.add('active');

        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(tabId).classList.add('active');

        this.currentTab = tabId;

        // Load tab-specific data
        this.loadTabData(tabId);
    }

    async loadTabData(tabId) {
        switch (tabId) {
            case 'models':
                await this.loadModels();
                break;
            case 'performance':
                await this.loadPerformanceData();
                break;
            case 'hardware':
                await this.loadHardwareData();
                break;
            case 'optimization':
                await this.loadOptimizationData();
                break;
        }
    }

    async loadModels() {
        try {
            const response = await fetch('/api/models');
            const models = await response.json();
            this.displayModels(models);
        } catch (error) {
            console.error('Failed to load models:', error);
        }
    }

    displayModels(models) {
        const modelsList = document.getElementById('modelsList');
        if (!modelsList) return;

        modelsList.innerHTML = '';

        models.forEach(model => {
            const modelItem = document.createElement('div');
            modelItem.className = 'model-item';
            modelItem.innerHTML = `
                <div class="model-header">
                    <div class="model-info">
                        <h3>${model.name}</h3>
                        <p>${model.description || 'No description available'}</p>
                    </div>
                    <div class="model-status ${model.status}">
                        <i class="fas fa-${this.getModelStatusIcon(model.status)}"></i>
                        ${model.status.charAt(0).toUpperCase() + model.status.slice(1)}
                    </div>
                </div>
                <div class="model-details">
                    <div class="model-specs">
                        <span class="spec-tag">${model.parameters || 'Unknown'} Parameters</span>
                        <span class="spec-tag">${model.quantization || 'FP16'}</span>
                        <span class="spec-tag">${model.size || 'Unknown'} GB</span>
                    </div>
                    <div class="model-actions">
                        <button class="btn btn-secondary" onclick="gerdsenAI.unloadModel('${model.id}')">
                            <i class="fas fa-stop"></i>
                            Unload
                        </button>
                        <button class="btn btn-primary" onclick="gerdsenAI.configureModel('${model.id}')">
                            <i class="fas fa-cog"></i>
                            Configure
                        </button>
                    </div>
                </div>
            `;
            modelsList.appendChild(modelItem);
        });
    }

    getModelStatusIcon(status) {
        switch (status) {
            case 'loaded': return 'play';
            case 'loading': return 'spinner fa-spin';
            case 'error': return 'exclamation-triangle';
            default: return 'pause';
        }
    }

    async handleModelFiles(files) {
        const fileArray = Array.from(files);
        const supportedExtensions = ['.mlx', '.gguf', '.safetensors', '.bin', '.mlpackage'];
        
        const validFiles = fileArray.filter(file => {
            return supportedExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
        });

        if (validFiles.length === 0) {
            this.showNotification('warning', 'Invalid Files', 'Please select supported model files (.mlx, .gguf, .safetensors, .bin, .mlpackage)');
            return;
        }

        this.showLoading('Uploading models...');

        try {
            for (const file of validFiles) {
                await this.uploadModel(file);
            }
            
            this.hideLoading();
            this.showNotification('success', 'Upload Complete', `Successfully uploaded ${validFiles.length} model(s)`);
            await this.loadModels(); // Refresh models list
            
        } catch (error) {
            this.hideLoading();
            this.showNotification('error', 'Upload Failed', error.message);
        }
    }

    async uploadModel(file) {
        const formData = new FormData();
        formData.append('model', file);

        const response = await fetch('/api/models/upload', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Failed to upload ${file.name}`);
        }

        return response.json();
    }

    async toggleAutoOptimization(enabled) {
        try {
            const response = await fetch('/api/optimization/auto', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ enabled })
            });

            if (response.ok) {
                this.showNotification('success', 'Auto Optimization', `Auto optimization ${enabled ? 'enabled' : 'disabled'}`);
            }
        } catch (error) {
            console.error('Failed to toggle auto optimization:', error);
        }
    }

    async updateOptimizationSetting(setting, value) {
        try {
            const response = await fetch('/api/optimization/settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ [setting]: value })
            });

            if (response.ok) {
                this.showNotification('info', 'Setting Updated', `${setting} has been updated`);
            }
        } catch (error) {
            console.error('Failed to update optimization setting:', error);
        }
    }

    async optimizeAllModels() {
        this.showLoading('Optimizing all models...');
        
        try {
            const response = await fetch('/api/optimization/optimize-all', {
                method: 'POST'
            });

            if (response.ok) {
                this.hideLoading();
                this.showNotification('success', 'Optimization Complete', 'All models have been optimized for Apple Silicon');
            }
        } catch (error) {
            this.hideLoading();
            this.showNotification('error', 'Optimization Failed', error.message);
        }
    }

    async clearModelCache() {
        try {
            const response = await fetch('/api/models/clear-cache', {
                method: 'POST'
            });

            if (response.ok) {
                this.showNotification('success', 'Cache Cleared', 'Model cache has been cleared');
            }
        } catch (error) {
            this.showNotification('error', 'Clear Failed', error.message);
        }
    }

    async benchmarkSystem() {
        this.showLoading('Running system benchmark...');
        
        try {
            const response = await fetch('/api/benchmark/run', {
                method: 'POST'
            });

            const result = await response.json();
            
            this.hideLoading();
            this.showNotification('success', 'Benchmark Complete', `System score: ${result.score}/100`);
            
        } catch (error) {
            this.hideLoading();
            this.showNotification('error', 'Benchmark Failed', error.message);
        }
    }

    async exportSettings() {
        try {
            const response = await fetch('/api/settings/export');
            const blob = await response.blob();
            
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'gerdsenai-settings.json';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            this.showNotification('success', 'Export Complete', 'Settings have been exported');
            
        } catch (error) {
            this.showNotification('error', 'Export Failed', error.message);
        }
    }

    minimizeToTray() {
        // Send message to main process to minimize to tray
        if (window.electronAPI) {
            window.electronAPI.minimizeToTray();
        } else {
            // Fallback for web version
            window.minimize();
        }
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'metrics_update':
                this.updateSystemMetrics(data.data);
                break;
            case 'hardware_update':
                this.updateHardwareInfo(data.data);
                break;
            case 'model_status':
                this.updateModelStatus(data.data);
                break;
            case 'optimization_status':
                this.updateOptimizationStatus(data.data);
                break;
            case 'notification':
                this.showNotification(data.level, data.title, data.message);
                break;
        }
    }

    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connectionStatus');
        const statusDot = statusElement?.querySelector('.status-dot');
        const statusText = statusElement?.querySelector('span');
        
        if (statusDot && statusText) {
            statusDot.className = `status-dot ${connected ? 'connected' : 'disconnected'}`;
            statusText.textContent = connected ? 'Connected' : 'Disconnected';
        }
    }

    updateElement(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
        }
    }

    updateProgressBar(elementId, percentage) {
        const element = document.getElementById(elementId);
        if (element) {
            element.style.width = `${Math.min(100, Math.max(0, percentage))}%`;
        }
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    showLoading(message = 'Loading...') {
        const overlay = document.getElementById('loadingOverlay');
        const text = overlay?.querySelector('.loading-text');
        
        if (overlay) {
            overlay.classList.add('active');
        }
        
        if (text) {
            text.textContent = message;
        }
    }

    hideLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.remove('active');
        }
    }

    showNotification(type, title, message) {
        const container = document.getElementById('notificationContainer');
        if (!container) return;

        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-header">
                <div class="notification-title">${title}</div>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="notification-message">${message}</div>
        `;

        container.appendChild(notification);

        // Show notification
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    handleSearch(query) {
        // Implement search functionality across all tabs
        console.log('Searching for:', query);
        // This would filter content based on the search query
    }

    // Utility methods for external access
    async unloadModel(modelId) {
        try {
            const response = await fetch(`/api/models/${modelId}/unload`, {
                method: 'POST'
            });

            if (response.ok) {
                this.showNotification('success', 'Model Unloaded', 'Model has been unloaded from memory');
                await this.loadModels();
            }
        } catch (error) {
            this.showNotification('error', 'Unload Failed', error.message);
        }
    }

    async configureModel(modelId) {
        // Open model configuration dialog
        console.log('Configuring model:', modelId);
        // This would open a modal or navigate to configuration page
    }

    // Cleanup method
    destroy() {
        // Clear all intervals
        Object.values(this.updateIntervals).forEach(interval => {
            clearInterval(interval);
        });

        // Close WebSocket connection
        if (this.wsConnection) {
            this.wsConnection.close();
        }

        // Destroy charts
        Object.values(this.charts).forEach(chart => {
            chart.destroy();
        });
    }
}

// Global functions for window controls
function minimizeToTray() {
    if (window.gerdsenAI) {
        window.gerdsenAI.minimizeToTray();
    }
}

function toggleMaximize() {
    if (window.electronAPI) {
        window.electronAPI.toggleMaximize();
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.gerdsenAI = new GerdsenAIManager();
});

// Handle page unload
window.addEventListener('beforeunload', () => {
    if (window.gerdsenAI) {
        window.gerdsenAI.destroy();
    }
});

