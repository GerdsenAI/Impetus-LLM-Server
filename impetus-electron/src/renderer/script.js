/**
 * IMPETUS Electron App - Renderer Script
 * Handles UI interactions and communicates with main process
 */

class ImpetusRenderer {
    constructor() {
        this.serverStatus = 'unknown';
        this.models = [];
        this.currentModel = null;
        this.refreshInterval = null;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.updateSystemInfo();
        this.refreshStatus();
        
        // Start periodic status updates
        this.startPeriodicUpdates();
        
        console.log('IMPETUS Renderer initialized');
    }
    
    setupEventListeners() {
        // Server control buttons
        document.getElementById('startServerBtn').addEventListener('click', () => {
            this.startServer();
        });
        
        document.getElementById('stopServerBtn').addEventListener('click', () => {
            this.stopServer();
        });
        
        document.getElementById('refreshStatusBtn').addEventListener('click', () => {
            this.refreshStatus();
        });
        
        // API endpoint link
        document.getElementById('apiEndpoint').addEventListener('click', (e) => {
            e.preventDefault();
            const url = e.target.textContent;
            window.electronAPI.openExternal(url);
        });
    }
    
    async updateSystemInfo() {
        try {
            document.getElementById('platform').textContent = window.electronAPI.getPlatform();
            document.getElementById('electronVersion').textContent = window.electronAPI.getVersion();
            
            // Request notification permission
            await window.electronAPI.requestNotificationPermission();
        } catch (error) {
            console.error('Failed to update system info:', error);
        }
    }
    
    async refreshStatus() {
        this.showLoading('Checking server status...');
        
        try {
            const status = await window.electronAPI.getServerStatus();
            
            this.serverStatus = status.status;
            this.models = status.models || [];
            this.currentModel = status.currentModel;
            
            this.updateUI();
            
        } catch (error) {
            console.error('Failed to refresh status:', error);
            this.showNotification('Error', 'Failed to refresh server status');
        } finally {
            this.hideLoading();
        }
    }
    
    updateUI() {
        this.updateServerStatus();
        this.updateServerControls();
        this.updateModels();
        this.updateServerInfo();
    }
    
    updateServerStatus() {
        const statusElement = document.getElementById('serverStatus');
        const indicatorElement = document.getElementById('statusIndicator');
        
        switch (this.serverStatus) {
            case 'running':
                statusElement.textContent = 'Running';
                statusElement.className = 'status-running';
                indicatorElement.textContent = '🟢';
                break;
            case 'stopped':
                statusElement.textContent = 'Stopped';
                statusElement.className = 'status-stopped';
                indicatorElement.textContent = '🔴';
                break;
            default:
                statusElement.textContent = 'Unknown';
                statusElement.className = 'status-loading';
                indicatorElement.textContent = '🟡';
        }
    }
    
    updateServerControls() {
        const startBtn = document.getElementById('startServerBtn');
        const stopBtn = document.getElementById('stopServerBtn');
        
        if (this.serverStatus === 'running') {
            startBtn.disabled = true;
            stopBtn.disabled = false;
        } else if (this.serverStatus === 'stopped') {
            startBtn.disabled = false;
            stopBtn.disabled = true;
        } else {
            startBtn.disabled = true;
            stopBtn.disabled = true;
        }
    }
    
    updateModels() {
        const container = document.getElementById('modelsContainer');
        
        if (this.models.length === 0) {
            container.innerHTML = `
                <div class="no-models">
                    <p>${this.serverStatus === 'running' ? 'No models loaded' : 'Start the server to see available models'}</p>
                </div>
            `;
            return;
        }
        
        const modelsHTML = this.models.map(model => `
            <div class="model-card ${model.id === this.currentModel ? 'active' : ''}">
                <div class="model-info">
                    <h3>${model.id}</h3>
                    <div class="model-details">
                        <span class="model-format">${model.format}</span>
                        ${model.capabilities ? model.capabilities.map(cap => `<span class="model-format">${cap}</span>`).join(' ') : ''}
                    </div>
                </div>
                <div class="model-actions">
                    ${model.id === this.currentModel ? 
                        '<span class="btn btn-small" style="background: #34c759;">Current</span>' :
                        `<button class="btn btn-small" onclick="impetusRenderer.switchModel('${model.id}')">Switch</button>`
                    }
                </div>
            </div>
        `).join('');
        
        container.innerHTML = modelsHTML;
    }
    
    updateServerInfo() {
        // Update API endpoint link
        const endpointElement = document.getElementById('apiEndpoint');
        const host = document.getElementById('serverHost').textContent;
        const port = document.getElementById('serverPort').textContent;
        const url = `http://${host}:${port}`;
        
        endpointElement.textContent = url;
        endpointElement.href = url;
    }
    
    async startServer() {
        this.showLoading('Starting IMPETUS server...');
        
        try {
            await window.electronAPI.startServer();
            this.showNotification('IMPETUS', 'Server is starting...');
            
            // Wait a moment then refresh status
            setTimeout(() => {
                this.refreshStatus();
            }, 3000);
            
        } catch (error) {
            console.error('Failed to start server:', error);
            this.showNotification('Error', 'Failed to start server');
        } finally {
            this.hideLoading();
        }
    }
    
    async stopServer() {
        this.showLoading('Stopping server...');
        
        try {
            await window.electronAPI.stopServer();
            this.showNotification('IMPETUS', 'Server stopped');
            this.refreshStatus();
            
        } catch (error) {
            console.error('Failed to stop server:', error);
            this.showNotification('Error', 'Failed to stop server');
        } finally {
            this.hideLoading();
        }
    }
    
    async switchModel(modelId) {
        this.showLoading(`Switching to model ${modelId}...`);
        
        try {
            await window.electronAPI.switchModel(modelId);
            this.showNotification('IMPETUS', `Switched to model: ${modelId}`);
            this.refreshStatus();
            
        } catch (error) {
            console.error('Failed to switch model:', error);
            this.showNotification('Error', `Failed to switch to model ${modelId}`);
        } finally {
            this.hideLoading();
        }
    }
    
    startPeriodicUpdates() {
        // Refresh status every 10 seconds
        this.refreshInterval = setInterval(() => {
            this.refreshStatus();
        }, 10000);
    }
    
    stopPeriodicUpdates() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
    
    showLoading(text = 'Loading...') {
        const overlay = document.getElementById('loadingOverlay');
        const loadingText = document.getElementById('loadingText');
        
        loadingText.textContent = text;
        overlay.classList.remove('hidden');
    }
    
    hideLoading() {
        const overlay = document.getElementById('loadingOverlay');
        overlay.classList.add('hidden');
    }
    
    showNotification(title, message, type = 'info') {
        // Use Electron notification if available
        if (window.electronAPI.showNotification) {
            window.electronAPI.showNotification(title, {
                body: message,
                silent: false
            });
        }
        
        // Also show in-app notification
        this.showInAppNotification(message, type);
    }
    
    showInAppNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div style="font-weight: 600; margin-bottom: 4px;">IMPETUS</div>
            <div>${message}</div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-out forwards';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
}

// Global functions for inline event handlers
function openVSCode() {
    // Try to open VS Code
    window.electronAPI.openExternal('vscode://');
}

function openAPI() {
    const host = document.getElementById('serverHost').textContent;
    const port = document.getElementById('serverPort').textContent;
    window.electronAPI.openExternal(`http://${host}:${port}/v1/models`);
}

function openLogs() {
    // This could open the log file or a log viewer
    impetusRenderer.showNotification('Info', 'Log viewer coming soon!');
}

function testConnection() {
    // Test the API connection
    fetch('http://localhost:8080/api/health')
        .then(response => response.json())
        .then(data => {
            impetusRenderer.showNotification('Success', 'Connection test successful!');
        })
        .catch(error => {
            impetusRenderer.showNotification('Error', 'Connection test failed');
        });
}

function showAbout() {
    alert(`IMPETUS - Intelligent Model Platform Enabling Taskbar Unified Server
    
Version: 1.0.0
Platform: ${window.electronAPI.getPlatform()}
Electron: ${window.electronAPI.getVersion()}

© 2025 GerdsenAI`);
}

function showSettings() {
    impetusRenderer.showNotification('Info', 'Settings panel coming soon!');
}

function openGitHub() {
    window.electronAPI.openExternal('https://github.com/gerdsenai/impetus-llm-server');
}

// Initialize the renderer when DOM is loaded
let impetusRenderer;

document.addEventListener('DOMContentLoaded', () => {
    impetusRenderer = new ImpetusRenderer();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (impetusRenderer) {
        impetusRenderer.stopPeriodicUpdates();
    }
});

// Add slideOut animation to CSS dynamically
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);