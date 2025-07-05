/**
 * Preload script for Impetus Electron app
 * Exposes safe APIs to the renderer process
 */

const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
    // Server management
    getServerStatus: () => ipcRenderer.invoke('get-server-status'),
    startServer: () => ipcRenderer.invoke('start-server'),
    stopServer: () => ipcRenderer.invoke('stop-server'),
    
    // Model management
    switchModel: (modelId) => ipcRenderer.invoke('switch-model', modelId),
    
    // Utilities
    openExternal: (url) => ipcRenderer.invoke('open-external', url),
    
    // App info
    getVersion: () => process.versions.electron,
    getPlatform: () => process.platform,
    
    // Notifications
    showNotification: (title, options) => {
        if (Notification.permission === 'granted') {
            return new Notification(title, options);
        }
    },
    
    requestNotificationPermission: () => {
        return Notification.requestPermission();
    }
});

// Console logging for debugging
window.addEventListener('DOMContentLoaded', () => {
    console.log('Impetus Electron preload script loaded');
    console.log('Electron version:', process.versions.electron);
    console.log('Node version:', process.versions.node);
    console.log('Chrome version:', process.versions.chrome);
});