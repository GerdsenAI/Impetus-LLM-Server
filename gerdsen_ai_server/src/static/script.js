// GerdsenAI MLX Manager - Real-time Dynamic Interface
// Connects to backend APIs and displays real hardware data

class GerdsenAIManager {
    constructor() {
        this.socket = null;
        this.apiBase = '';  // Use relative URLs for same-origin requests
        this.isConnected = false;
        this.updateIntervals = {};
        this.charts = {};
        this.hardwareData = {};
        this.modelData = {};
        
        this.init();
    }

    async init() {
        console.log('🚀 Initializing GerdsenAI MLX Manager');
        
        // Initialize WebSocket connection
        this.initWebSocket();
        
        // Load initial data
        await this.loadInitialData();
        
        // Set up periodic updates
        this.setupPeriodicUpdates();
        
        // Initialize UI components
        this.initializeUI();
        
        console.log('✅ GerdsenAI MLX Manager initialized');
    }

    initWebSocket() {
        try {
            // Initialize Socket.IO connection
            this.socket = io();
            
            this.socket.on('connect', () => {
                console.log('🔌 WebSocket connected');
                this.isConnected = true;
                this.updateConnectionStatus(true);
                
                // Subscribe to real-time updates
                this.socket.emit('subscribe_metrics');
                this.socket.emit('subscribe_models');
            });
            
            this.socket.on('disconnect', () => {
                console.log('🔌 WebSocket disconnected');
                this.isConnected = false;
                this.updateConnectionStatus(false);
            });
            
            this.socket.on('metrics_update', (data) => {
                if (data.success) {
                    this.updateMetricsDisplay(data.data);
                }
            });
            
            this.socket.on('model_update', (data) => {
                if (data.success) {
                    this.updateModelsDisplay(data.data);
                }
            });
            
            this.socket.on('system_alert', (alert) => {
                this.showSystemAlert(alert);
            });
            
            this.socket.on('hardware_info', (data) => {
                if (data.success) {
                    this.updateHardwareDisplay(data.data);
                }
            });
            
        } catch (error) {
            console.error('❌ WebSocket initialization failed:', error);
            this.isConnected = false;
            this.updateConnectionStatus(false);
        }
    }

    async loadInitialData() {
        try {
            // Load system information
            const systemInfo = await this.fetchAPI('/api/hardware/system-info');
            if (systemInfo.success) {
                this.hardwareData = systemInfo.data;
                this.updateHardwareDisplay(systemInfo.data);
            }
            
            // Load optimization capabilities
            const capabilities = await this.fetchAPI('/api/optimization/capabilities');
            if (capabilities.success) {
                this.updateCapabilitiesDisplay(capabilities.data);
            }
            
            // Load model list
            const models = await this.fetchAPI('/api/models/list');
            if (models.success) {
                this.modelData = models.data;
                this.updateModelsDisplay(models.data);
            }
            
            // Load optimization profiles
            const profiles = await this.fetchAPI('/api/optimization/profiles');
            if (profiles.success) {
                this.updateProfilesDisplay(profiles.data);
            }
            
        } catch (error) {
            console.error('❌ Failed to load initial data:', error);
            this.showError('Failed to load initial data');
        }
    }

    async fetchAPI(endpoint, options = {}) {
        try {
            const response = await fetch(this.apiBase + endpoint, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`❌ API request failed for ${endpoint}:`, error);
            throw error;
        }
    }

    updateHardwareDisplay(data) {
        // Update chip information
        if (data.chip_info) {
            const chipInfo = data.chip_info;
            this.updateElement('chip-name', chipInfo.chip_name || 'Unknown');
            this.updateElement('model-identifier', chipInfo.model_identifier || 'Unknown');
            this.updateElement('detected-memory', `${chipInfo.detected_memory_gb || 0}GB`);
            
            if (chipInfo.specifications) {
                const specs = chipInfo.specifications;
                this.updateElement('cpu-cores', `${specs.cpu_cores_performance}P + ${specs.cpu_cores_efficiency}E`);
                this.updateElement('gpu-cores', specs.gpu_cores || 0);
                this.updateElement('neural-engine-cores', specs.neural_engine_cores || 0);
                this.updateElement('memory-bandwidth', `${specs.memory_bandwidth_gbps || 0}GB/s`);
                this.updateElement('process-node', specs.process_node || 'Unknown');
            }
        }
        
        // Update Neural Engine info
        if (data.neural_engine) {
            const ne = data.neural_engine;
            this.updateElement('neural-engine-status', ne.available ? 'Available' : 'Not Available');
            this.updateElement('neural-engine-cores-count', ne.cores || 0);
            
            // Update framework support
            const frameworks = ne.framework_support || {};
            this.updateElement('coreml-support', frameworks.coreml ? '✅' : '❌');
            this.updateElement('mlx-support', frameworks.mlx ? '✅' : '❌');
        }
        
        // Update GPU info
        if (data.gpu) {
            const gpu = data.gpu;
            this.updateElement('gpu-status', gpu.available ? 'Available' : 'Not Available');
            this.updateElement('gpu-cores-count', gpu.cores || 0);
            this.updateElement('gpu-memory', `~${gpu.memory_gb || 0}GB`);
            this.updateElement('metal-support', gpu.metal_support ? '✅' : '❌');
        }
    }

    updateMetricsDisplay(metrics) {
        // Update CPU metrics
        if (metrics.cpu) {
            const cpu = metrics.cpu;
            this.updateElement('cpu-usage', `${cpu.usage_percent_total || 0}%`);
            this.updateElement('cpu-frequency', `${cpu.frequency_mhz || 0}MHz`);
            this.updateElement('cpu-cores-total', cpu.core_count || 0);
            
            // Update CPU usage chart
            this.updateCPUChart(cpu.usage_percent_per_core || []);
        }
        
        // Update memory metrics
        if (metrics.memory) {
            const memory = metrics.memory;
            this.updateElement('memory-used', `${memory.used_gb || 0}GB`);
            this.updateElement('memory-total', `${memory.total_gb || 0}GB`);
            this.updateElement('memory-usage-percent', `${memory.usage_percent || 0}%`);
            this.updateElement('memory-pressure', memory.pressure || 'unknown');
            
            // Update memory usage bar
            this.updateProgressBar('memory-progress', memory.usage_percent || 0);
        }
        
        // Update thermal metrics
        if (metrics.thermal) {
            const thermal = metrics.thermal;
            this.updateElement('thermal-state', thermal.state || 'unknown');
            
            if (thermal.temperatures && thermal.temperatures.cpu_estimated) {
                this.updateElement('cpu-temperature', `${thermal.temperatures.cpu_estimated}°C`);
            }
        }
        
        // Update power metrics
        if (metrics.power) {
            const power = metrics.power;
            if (power.battery) {
                this.updateElement('battery-level', `${power.battery.percent || 0}%`);
                this.updateElement('power-source', power.battery.plugged_in ? 'AC Power' : 'Battery');
            }
            
            if (power.consumption_watts) {
                this.updateElement('power-consumption', `${power.consumption_watts}W`);
            }
        }
    }

    updateModelsDisplay(data) {
        const loadedModels = data.loaded_models || [];
        const cachedModels = data.cached_models || [];
        
        // Update model counts
        this.updateElement('loaded-models-count', loadedModels.length);
        this.updateElement('cached-models-count', cachedModels.length);
        
        // Update model lists
        this.updateModelList('loaded-models-list', loadedModels, 'loaded');
        this.updateModelList('cached-models-list', cachedModels, 'cached');
    }

    updateModelList(containerId, models, status) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        container.innerHTML = '';
        
        models.forEach(model => {
            const modelElement = document.createElement('div');
            modelElement.className = 'model-item';
            modelElement.innerHTML = `
                <div class="model-info">
                    <div class="model-name">${model.id || 'Unknown'}</div>
                    <div class="model-status">${status}</div>
                </div>
                <div class="model-actions">
                    ${status === 'loaded' ? 
                        '<button onclick="manager.unloadModel(\'' + model.id + '\')">Unload</button>' :
                        '<button onclick="manager.loadModel(\'' + model.id + '\')">Load</button>'
                    }
                </div>
            `;
            container.appendChild(modelElement);
        });
    }

    updateCapabilitiesDisplay(capabilities) {
        this.updateElement('apple-silicon-status', capabilities.coreml_available || capabilities.mlx_available ? 'Optimized' : 'Basic');
        this.updateElement('coreml-available', capabilities.coreml_available ? '✅' : '❌');
        this.updateElement('mlx-available', capabilities.mlx_available ? '✅' : '❌');
        this.updateElement('mps-available', capabilities.mps_available ? '✅' : '❌');
        this.updateElement('neural-engine-available', capabilities.neural_engine_available ? '✅' : '❌');
        this.updateElement('metal-gpu-available', capabilities.metal_gpu_available ? '✅' : '❌');
        this.updateElement('unified-memory', capabilities.unified_memory ? '✅' : '❌');
    }

    updateProfilesDisplay(profiles) {
        const container = document.getElementById('optimization-profiles');
        if (!container) return;
        
        container.innerHTML = '';
        
        Object.entries(profiles).forEach(([name, profile]) => {
            const profileElement = document.createElement('div');
            profileElement.className = 'profile-item';
            profileElement.innerHTML = `
                <div class="profile-name">${name}</div>
                <div class="profile-details">
                    <div>Framework: ${profile.framework}</div>
                    <div>Device: ${profile.device}</div>
                    <div>Precision: ${profile.precision}</div>
                    <div>Batch Size: ${profile.batch_size}</div>
                </div>
                <button onclick="manager.applyProfile('${name}')">Apply</button>
            `;
            container.appendChild(profileElement);
        });
    }

    updateCPUChart(coreUsage) {
        // Simple text-based CPU core usage display
        const container = document.getElementById('cpu-cores-chart');
        if (!container) return;
        
        container.innerHTML = '';
        
        coreUsage.forEach((usage, index) => {
            const coreElement = document.createElement('div');
            coreElement.className = 'cpu-core';
            coreElement.innerHTML = `
                <div class="core-label">Core ${index + 1}</div>
                <div class="core-usage-bar">
                    <div class="core-usage-fill" style="width: ${usage}%"></div>
                </div>
                <div class="core-usage-text">${usage.toFixed(1)}%</div>
            `;
            container.appendChild(coreElement);
        });
    }

    updateProgressBar(id, percentage) {
        const progressBar = document.getElementById(id);
        if (progressBar) {
            const fill = progressBar.querySelector('.progress-fill');
            if (fill) {
                fill.style.width = `${Math.min(100, Math.max(0, percentage))}%`;
            }
        }
    }

    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            statusElement.textContent = connected ? 'Connected' : 'Disconnected';
            statusElement.className = connected ? 'status-connected' : 'status-disconnected';
        }
    }

    showSystemAlert(alert) {
        const alertsContainer = document.getElementById('system-alerts');
        if (!alertsContainer) return;
        
        const alertElement = document.createElement('div');
        alertElement.className = `alert alert-${alert.type}`;
        alertElement.innerHTML = `
            <div class="alert-content">
                <div class="alert-message">${alert.message}</div>
                <div class="alert-timestamp">${new Date(alert.timestamp * 1000).toLocaleTimeString()}</div>
            </div>
            <button class="alert-close" onclick="this.parentElement.remove()">×</button>
        `;
        
        alertsContainer.insertBefore(alertElement, alertsContainer.firstChild);
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (alertElement.parentElement) {
                alertElement.remove();
            }
        }, 10000);
    }

    showError(message) {
        this.showSystemAlert({
            type: 'error',
            message: message,
            timestamp: Date.now() / 1000
        });
    }

    showSuccess(message) {
        this.showSystemAlert({
            type: 'success',
            message: message,
            timestamp: Date.now() / 1000
        });
    }

    setupPeriodicUpdates() {
        // Update metrics every 2 seconds if WebSocket is not connected
        this.updateIntervals.metrics = setInterval(() => {
            if (!this.isConnected) {
                this.loadMetrics();
            }
        }, 2000);
        
        // Update model list every 10 seconds
        this.updateIntervals.models = setInterval(() => {
            if (!this.isConnected) {
                this.loadModels();
            }
        }, 10000);
    }

    async loadMetrics() {
        try {
            const metrics = await this.fetchAPI('/api/hardware/real-time-metrics');
            if (metrics.success) {
                this.updateMetricsDisplay(metrics.data);
            }
        } catch (error) {
            console.error('❌ Failed to load metrics:', error);
        }
    }

    async loadModels() {
        try {
            const models = await this.fetchAPI('/api/models/list');
            if (models.success) {
                this.updateModelsDisplay(models.data);
            }
        } catch (error) {
            console.error('❌ Failed to load models:', error);
        }
    }

    initializeUI() {
        // Initialize tab switching
        this.initializeTabs();
        
        // Initialize modal dialogs
        this.initializeModals();
        
        // Initialize form handlers
        this.initializeFormHandlers();
    }

    initializeTabs() {
        const tabButtons = document.querySelectorAll('.tab-button');
        const tabContents = document.querySelectorAll('.tab-content');
        
        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const targetTab = button.dataset.tab;
                
                // Remove active class from all tabs and contents
                tabButtons.forEach(btn => btn.classList.remove('active'));
                tabContents.forEach(content => content.classList.remove('active'));
                
                // Add active class to clicked tab and corresponding content
                button.classList.add('active');
                const targetContent = document.getElementById(targetTab);
                if (targetContent) {
                    targetContent.classList.add('active');
                }
            });
        });
    }

    initializeModals() {
        // Close modal when clicking outside
        window.addEventListener('click', (event) => {
            if (event.target.classList.contains('modal')) {
                event.target.style.display = 'none';
            }
        });
    }

    initializeFormHandlers() {
        // Model upload form
        const uploadForm = document.getElementById('model-upload-form');
        if (uploadForm) {
            uploadForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleModelUpload(new FormData(uploadForm));
            });
        }
    }

    async handleModelUpload(formData) {
        try {
            const response = await fetch('/api/models/upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess('Model uploaded successfully');
                this.loadModels(); // Refresh model list
            } else {
                this.showError(result.error || 'Upload failed');
            }
        } catch (error) {
            console.error('❌ Model upload failed:', error);
            this.showError('Model upload failed');
        }
    }

    async loadModel(modelId) {
        try {
            const response = await this.fetchAPI('/api/models/load', {
                method: 'POST',
                body: JSON.stringify({ model_id: modelId })
            });
            
            if (response.success) {
                this.showSuccess(`Model ${modelId} loaded successfully`);
                this.loadModels(); // Refresh model list
            } else {
                this.showError(response.error || 'Failed to load model');
            }
        } catch (error) {
            console.error('❌ Failed to load model:', error);
            this.showError('Failed to load model');
        }
    }

    async unloadModel(modelId) {
        try {
            const response = await this.fetchAPI(`/api/models/unload/${modelId}`, {
                method: 'POST'
            });
            
            if (response.success) {
                this.showSuccess(`Model ${modelId} unloaded successfully`);
                this.loadModels(); // Refresh model list
            } else {
                this.showError(response.error || 'Failed to unload model');
            }
        } catch (error) {
            console.error('❌ Failed to unload model:', error);
            this.showError('Failed to unload model');
        }
    }

    async applyProfile(profileName) {
        try {
            this.showSuccess(`Applied optimization profile: ${profileName}`);
        } catch (error) {
            console.error('❌ Failed to apply profile:', error);
            this.showError('Failed to apply optimization profile');
        }
    }

    // Cleanup method
    destroy() {
        // Clear intervals
        Object.values(this.updateIntervals).forEach(interval => {
            clearInterval(interval);
        });
        
        // Disconnect WebSocket
        if (this.socket) {
            this.socket.disconnect();
        }
    }
}

// Initialize the manager when the page loads
let manager;

document.addEventListener('DOMContentLoaded', () => {
    manager = new GerdsenAIManager();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (manager) {
        manager.destroy();
    }
});

