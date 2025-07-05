/**
 * Main Electron process for IMPETUS
 * Intelligent Model Platform Enabling Taskbar Unified Server
 */

const { app, BrowserWindow, Menu, Tray, ipcMain, dialog, shell, nativeImage } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const axios = require('axios');
const Store = require('electron-store');

// Initialize persistent store
const store = new Store();

class ImpetusApp {
    constructor() {
        this.mainWindow = null;
        this.tray = null;
        this.serverProcess = null;
        this.serverPort = 8080;
        this.serverHost = 'localhost';
        this.serverStatus = 'stopped';
        this.loadedModels = [];
        this.currentModel = null;
        
        // Model directory paths (dynamic based on user)
        this.userHome = os.homedir();
        this.modelsBaseDir = path.join(this.userHome, 'Models');
        
        // Initialize app
        this.init();
    }
    
    init() {
        // Set app properties
        app.setName('IMPETUS');
        app.setAboutPanelOptions({
            applicationName: 'IMPETUS',
            applicationVersion: app.getVersion(),
            version: app.getVersion(),
            copyright: 'Copyright © 2025 GerdsenAI',
            credits: 'Intelligent Model Platform Enabling Taskbar Unified Server\n\nBy GerdsenAI - "Intelligence Without Boundaries"\n\nLocal-first AI that respects your privacy.',
            website: 'https://gerdsenai.com'
        });
        
        // App event handlers
        app.whenReady().then(() => {
            this.createTray();
            this.loadSettings();
            this.checkServerStatus();
            
            // Hide dock icon on macOS for menu bar app experience
            if (process.platform === 'darwin') {
                app.dock.hide();
            }
        });
        
        app.on('window-all-closed', (event) => {
            // Prevent app from quitting when all windows are closed
            event.preventDefault();
        });
        
        app.on('activate', () => {
            if (this.mainWindow === null) {
                this.createWindow();
            }
        });
        
        app.on('before-quit', () => {
            this.cleanup();
        });
        
        // IPC handlers
        this.setupIpcHandlers();
    }
    
    createWindow() {
        this.mainWindow = new BrowserWindow({
            width: 1200,
            height: 800,
            minWidth: 800,
            minHeight: 600,
            webPreferences: {
                nodeIntegration: false,
                contextIsolation: true,
                preload: path.join(__dirname, 'preload.js')
            },
            titleBarStyle: 'hiddenInset',
            show: false,
            icon: this.getAppIcon()
        });
        
        // Load the UI
        this.mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));
        
        // Show window when ready
        this.mainWindow.once('ready-to-show', () => {
            this.mainWindow.show();
        });
        
        // Handle window closed
        this.mainWindow.on('closed', () => {
            this.mainWindow = null;
        });
        
        // Handle window minimize to tray
        this.mainWindow.on('minimize', (event) => {
            if (process.platform === 'darwin') {
                event.preventDefault();
                this.mainWindow.hide();
            }
        });
        
        // Development tools
        if (process.env.NODE_ENV === 'development') {
            this.mainWindow.webContents.openDevTools();
        }
    }
    
    createTray() {
        // Create tray icon
        const iconPath = this.getTrayIcon();
        this.tray = new Tray(iconPath);
        
        this.updateTrayTooltip();
        this.updateTrayMenu();
        
        // Tray click handlers
        this.tray.on('click', () => {
            this.showWindow();
        });
        
        this.tray.on('right-click', () => {
            this.tray.popUpContextMenu();
        });
    }
    
    updateTrayMenu() {
        const contextMenu = Menu.buildFromTemplate([
            {
                label: 'IMPETUS',
                type: 'normal',
                enabled: false
            },
            { type: 'separator' },
            {
                label: `Server: ${this.serverStatus}`,
                type: 'normal',
                enabled: false
            },
            {
                label: this.serverStatus === 'running' ? 'Stop Server' : 'Start Server',
                type: 'normal',
                click: () => {
                    if (this.serverStatus === 'running') {
                        this.stopServer();
                    } else {
                        this.startServer();
                    }
                }
            },
            { type: 'separator' },
            {
                label: 'Models',
                type: 'submenu',
                submenu: this.buildModelsMenu()
            },
            { type: 'separator' },
            {
                label: 'Show Window',
                type: 'normal',
                click: () => this.showWindow()
            },
            {
                label: 'Settings',
                type: 'normal',
                click: () => this.showSettings()
            },
            { type: 'separator' },
            {
                label: 'About IMPETUS',
                type: 'normal',
                click: () => {
                    app.showAboutPanel();
                }
            },
            {
                label: 'Quit',
                type: 'normal',
                click: () => {
                    app.quit();
                }
            }
        ]);
        
        this.tray.setContextMenu(contextMenu);
    }
    
    buildModelsMenu() {
        const menu = [];
        
        // Add "Open Models Directory" option
        menu.push({
            label: 'Open Models Directory',
            type: 'normal',
            click: () => {
                if (this.modelsBaseDir) {
                    shell.openPath(this.modelsBaseDir).catch(err => {
                        console.error('Error opening models directory:', err);
                        dialog.showErrorBox('Error', `Could not open models directory: ${err.message}`);
                    });
                } else {
                    console.error('Models base directory not set');
                    dialog.showErrorBox('Error', 'Models directory path not configured');
                }
            }
        });
        
        menu.push({
            label: 'Scan for Models',
            type: 'normal',
            click: async () => {
                const result = await this.scanUserModels();
                if (result.success) {
                    dialog.showMessageBox(null, {
                        type: 'info',
                        title: 'Model Scan Complete',
                        message: `Found ${result.models.length} models`,
                        detail: `Models directory: ${result.directory}`
                    });
                } else {
                    dialog.showErrorBox('Scan Error', result.error);
                }
            }
        });
        
        menu.push({ type: 'separator' });
        
        if (this.loadedModels.length === 0) {
            menu.push({
                label: 'No models loaded',
                type: 'normal',
                enabled: false
            });
        } else {
            this.loadedModels.forEach(model => {
                menu.push({
                    label: `${model.id} (${model.format})`,
                    type: 'radio',
                    checked: model.id === this.currentModel,
                    click: () => this.switchToModel(model.id)
                });
            });
        }
        
        return menu;
    }
    
    updateTrayTooltip() {
        const status = this.serverStatus === 'running' ? '🟢' : '🔴';
        const models = this.loadedModels.length;
        this.tray.setToolTip(`IMPETUS ${status} | ${models} models loaded`);
    }
    
    showWindow() {
        if (this.mainWindow === null) {
            this.createWindow();
        } else {
            if (this.mainWindow.isMinimized()) {
                this.mainWindow.restore();
            }
            this.mainWindow.show();
            this.mainWindow.focus();
        }
    }
    
    showSettings() {
        // TODO: Implement settings window
        dialog.showMessageBox(null, {
            type: 'info',
            title: 'Settings',
            message: 'Settings panel coming soon!',
            detail: 'Server configuration and model management settings will be available here.'
        });
    }
    
    async startServer() {
        try {
            console.log('Starting IMPETUS server...');
            
            // Get paths to Python and server
            const pythonPath = this.getPythonPath();
            const serverPath = this.getServerPath();
            const workingDir = this.getWorkingDirectory();
            
            console.log('Python path:', pythonPath);
            console.log('Server path:', serverPath);
            console.log('Working directory:', workingDir);
            
            this.serverProcess = spawn(pythonPath, [serverPath], {
                cwd: workingDir,
                env: {
                    ...process.env,
                    PYTHONPATH: workingDir
                }
            });
            
            this.serverProcess.stdout.on('data', (data) => {
                console.log(`Server stdout: ${data}`);
            });
            
            this.serverProcess.stderr.on('data', (data) => {
                console.log(`Server stderr: ${data}`);
            });
            
            this.serverProcess.on('close', (code) => {
                console.log(`Server process exited with code ${code}`);
                this.serverStatus = 'stopped';
                this.updateTrayMenu();
                this.updateTrayTooltip();
            });
            
            // Wait a moment for server to start
            setTimeout(() => {
                this.checkServerStatus();
            }, 3000);
            
        } catch (error) {
            console.error('Failed to start server:', error);
            dialog.showErrorBox('Server Error', `Failed to start server: ${error.message}`);
        }
    }
    
    async stopServer() {
        if (this.serverProcess) {
            console.log('Stopping IMPETUS server...');
            this.serverProcess.kill('SIGTERM');
            this.serverProcess = null;
            this.serverStatus = 'stopped';
            this.loadedModels = [];
            this.currentModel = null;
            this.updateTrayMenu();
            this.updateTrayTooltip();
        }
    }
    
    async checkServerStatus() {
        try {
            const response = await axios.get(`http://${this.serverHost}:${this.serverPort}/api/health`, {
                timeout: 2000
            });
            
            if (response.status === 200) {
                this.serverStatus = 'running';
                await this.updateModels();
            } else {
                this.serverStatus = 'stopped';
            }
        } catch (error) {
            this.serverStatus = 'stopped';
        }
        
        this.updateTrayMenu();
        this.updateTrayTooltip();
    }
    
    async updateModels() {
        try {
            const response = await axios.get(`http://${this.serverHost}:${this.serverPort}/v1/models`);
            
            if (response.status === 200) {
                this.loadedModels = response.data.data.map(model => ({
                    id: model.id,
                    format: model.format || 'unknown',
                    capabilities: model.capabilities || []
                }));
                
                // Set current model to first available if none selected
                if (!this.currentModel && this.loadedModels.length > 0) {
                    this.currentModel = this.loadedModels[0].id;
                }
            }
        } catch (error) {
            console.error('Failed to fetch models:', error);
            this.loadedModels = [];
        }
    }
    
    async switchToModel(modelId) {
        try {
            const response = await axios.post(`http://${this.serverHost}:${this.serverPort}/v1/models/${modelId}/switch`);
            
            if (response.status === 200) {
                this.currentModel = modelId;
                this.updateTrayMenu();
                
                // Show notification
                if (Notification.permission === 'granted') {
                    new Notification('IMPETUS', {
                        body: `Switched to model: ${modelId}`,
                        icon: this.getAppIcon()
                    });
                }
            }
        } catch (error) {
            console.error('Failed to switch model:', error);
            dialog.showErrorBox('Model Switch Error', `Failed to switch to model ${modelId}: ${error.message}`);
        }
    }
    
    getPythonPath() {
        const fs = require('fs');
        
        // First try to use bundled Python environment
        const bundledPython = this.getBundledPythonPath();
        if (bundledPython && fs.existsSync(bundledPython)) {
            console.log('Using bundled Python:', bundledPython);
            return bundledPython;
        }
        
        // Try to use development virtual environment Python
        const venvPython = path.join(__dirname, '..', '..', 'venv', 'bin', 'python');
        if (fs.existsSync(venvPython)) {
            console.log('Using development Python:', venvPython);
            return venvPython;
        }
        
        // Fallback to system Python
        console.log('Using system Python');
        return process.platform === 'win32' ? 'python' : 'python3';
    }
    
    getBundledPythonPath() {
        // Get the path to the bundled Python environment
        if (app.isPackaged) {
            // In production, Python bundle is in Resources/
            const resourcesPath = process.resourcesPath;
            const bundlePath = path.join(resourcesPath, 'python-bundle');
            
            if (process.platform === 'win32') {
                return path.join(bundlePath, 'venv', 'Scripts', 'python.exe');
            } else {
                return path.join(bundlePath, 'venv', 'bin', 'python');
            }
        } else {
            // In development, Python bundle is in resources/
            const bundlePath = path.join(__dirname, '..', 'resources', 'python-bundle');
            
            if (process.platform === 'win32') {
                return path.join(bundlePath, 'venv', 'Scripts', 'python.exe');
            } else {
                return path.join(bundlePath, 'venv', 'bin', 'python');
            }
        }
    }
    
    getServerPath() {
        const fs = require('fs');
        
        // First try to use bundled server
        const bundledServer = this.getBundledServerPath();
        if (bundledServer && fs.existsSync(bundledServer)) {
            console.log('Using bundled server:', bundledServer);
            return bundledServer;
        }
        
        // Fallback to development server
        const devServer = path.join(__dirname, '..', '..', 'gerdsen_ai_server', 'src', 'production_main.py');
        console.log('Using development server:', devServer);
        return devServer;
    }
    
    getBundledServerPath() {
        // Get the path to the bundled server
        if (app.isPackaged) {
            // In production, Python bundle is in Resources/
            const resourcesPath = process.resourcesPath;
            return path.join(resourcesPath, 'python-bundle', 'src', 'production_main.py');
        } else {
            // In development, Python bundle is in resources/
            return path.join(__dirname, '..', 'resources', 'python-bundle', 'src', 'production_main.py');
        }
    }
    
    getWorkingDirectory() {
        const fs = require('fs');
        
        // If using bundled environment, work from the bundle directory
        const bundledServer = this.getBundledServerPath();
        if (bundledServer && fs.existsSync(bundledServer)) {
            if (app.isPackaged) {
                return path.join(process.resourcesPath, 'python-bundle', 'src');
            } else {
                return path.join(__dirname, '..', 'resources', 'python-bundle', 'src');
            }
        }
        
        // Fallback to development directory
        return path.join(__dirname, '..', '..');
    }
    
    getAppIcon() {
        // For now, use a built-in icon. In production, this would be a custom icon.
        return nativeImage.createFromNamedImage('NSApplicationIcon');
    }
    
    getTrayIcon() {
        // Create a simple tray icon
        const icon = nativeImage.createEmpty();
        
        // For now, use a system icon. In production, this would be a custom icon.
        if (process.platform === 'darwin') {
            return nativeImage.createFromNamedImage('NSStatusNone');
        }
        
        return icon;
    }
    
    loadSettings() {
        this.serverPort = store.get('serverPort', 8080);
        this.serverHost = store.get('serverHost', 'localhost');
    }
    
    saveSettings() {
        store.set('serverPort', this.serverPort);
        store.set('serverHost', this.serverHost);
    }
    
    setupIpcHandlers() {
        ipcMain.handle('get-server-status', () => {
            return {
                status: this.serverStatus,
                host: this.serverHost,
                port: this.serverPort,
                models: this.loadedModels,
                currentModel: this.currentModel
            };
        });
        
        ipcMain.handle('start-server', () => {
            return this.startServer();
        });
        
        ipcMain.handle('stop-server', () => {
            return this.stopServer();
        });
        
        ipcMain.handle('switch-model', (event, modelId) => {
            return this.switchToModel(modelId);
        });
        
        ipcMain.handle('open-external', (event, url) => {
            shell.openExternal(url);
        });
        
        ipcMain.handle('open-models-directory', () => {
            // Open the user's models directory in Finder/Explorer
            shell.openPath(this.modelsBaseDir);
            return { success: true, path: this.modelsBaseDir };
        });
        
        ipcMain.handle('scan-models', async () => {
            // Scan for models in the user's directory
            return this.scanUserModels();
        });
    }
    
    async scanUserModels() {
        try {
            // Ensure models directory exists
            if (!fs.existsSync(this.modelsBaseDir)) {
                fs.mkdirSync(this.modelsBaseDir, { recursive: true });
            }
            
            const models = [];
            const supportedExtensions = ['.gguf', '.safetensors', '.mlx', '.mlmodel', '.pt', '.pth', '.bin', '.onnx'];
            
            // Scan each format directory
            const formatDirs = ['GGUF', 'SafeTensors', 'MLX', 'CoreML', 'PyTorch', 'ONNX', 'Universal'];
            
            for (const formatDir of formatDirs) {
                const formatPath = path.join(this.modelsBaseDir, formatDir);
                if (fs.existsSync(formatPath)) {
                    // Scan capability subdirectories
                    const capabilities = ['chat', 'completion', 'embedding', 'vision', 'audio', 'multimodal'];
                    
                    for (const capability of capabilities) {
                        const capPath = path.join(formatPath, capability);
                        if (fs.existsSync(capPath)) {
                            const files = fs.readdirSync(capPath);
                            
                            for (const file of files) {
                                const ext = path.extname(file).toLowerCase();
                                if (supportedExtensions.includes(ext)) {
                                    const filePath = path.join(capPath, file);
                                    const stats = fs.statSync(filePath);
                                    
                                    models.push({
                                        name: path.basename(file, ext),
                                        path: filePath,
                                        format: formatDir.toLowerCase(),
                                        capability: capability,
                                        size: stats.size,
                                        sizeMB: (stats.size / (1024 * 1024)).toFixed(2),
                                        modified: stats.mtime
                                    });
                                }
                            }
                        }
                    }
                }
            }
            
            return { success: true, models: models, directory: this.modelsBaseDir };
        } catch (error) {
            console.error('Error scanning models:', error);
            return { success: false, error: error.message, directory: this.modelsBaseDir };
        }
    }
    
    cleanup() {
        this.saveSettings();
        if (this.serverProcess) {
            this.serverProcess.kill('SIGTERM');
        }
    }
}

// Create app instance
const impetusApp = new ImpetusApp();