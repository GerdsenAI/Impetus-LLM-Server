# IMPETUS Electron App

**Intelligent Model Platform Enabling Taskbar Unified Server**

A native macOS menubar/taskbar application for managing the IMPETUS LLM Server. This Electron app provides a clean, native interface for starting/stopping the server, switching between models, and monitoring server status.

## Features

- 🖥️ **Native macOS menubar integration**
- 🚀 **Start/stop IMPETUS server with one click**
- 🔄 **Dynamic model switching**
- 📊 **Real-time server status monitoring**
- ⚡ **Quick access to common actions**
- 🎨 **Apple HIG compliant design**
- 🔔 **Native notifications**

## Installation

### Prerequisites

- Node.js 16+ 
- Python 3.11+ (for the IMPETUS server)
- macOS 12+ (for optimal experience)

### Setup

1. **Install dependencies:**
   ```bash
   cd impetus-electron
   npm install
   ```

2. **Development mode:**
   ```bash
   npm run dev
   ```

3. **Build for production:**
   ```bash
   npm run build-mac
   ```

## Usage

### Menu Bar App

The app runs as a menubar application with these features:

- **Server Control**: Start/stop the IMPETUS Python server
- **Model Management**: View loaded models and switch between them
- **Quick Actions**: Access VS Code, API docs, and logs
- **Status Monitoring**: Real-time server and model status

### Main Window

Double-click the menubar icon to open the main window with:

- **Server Control Panel**: Start/stop server with visual feedback
- **Model Browser**: List of loaded models with switching capability
- **System Information**: Platform and version details
- **Quick Actions**: Common development tasks

## Architecture

```
impetus-electron/
├── src/
│   ├── main.js          # Main Electron process
│   ├── preload.js       # Secure IPC bridge
│   └── renderer/        # UI components
│       ├── index.html   # Main window
│       ├── styles.css   # Apple HIG styles
│       └── script.js    # UI logic
├── resources/           # App icons and assets
└── package.json         # Dependencies and build config
```

### Key Components

1. **Main Process** (`main.js`):
   - Creates tray icon and context menu
   - Manages Python server subprocess
   - Handles server status monitoring
   - Provides IPC APIs to renderer

2. **Preload Script** (`preload.js`):
   - Secure bridge between main and renderer
   - Exposes limited APIs through contextBridge

3. **Renderer Process** (`renderer/`):
   - Native-looking UI with Apple HIG compliance
   - Real-time status updates
   - Model management interface

## API Integration

The Electron app communicates with the IMPETUS server through:

- **Health Check**: `GET /api/health`
- **Model List**: `GET /v1/models`
- **Model Switch**: `POST /v1/models/{id}/switch`
- **Server Status**: WebSocket for real-time updates

## Development

### Running in Development

```bash
# Start with hot reload
npm run dev

# Watch for changes
npm run watch
```

### Building

```bash
# Build for current platform
npm run build

# Build macOS specific
npm run build-mac

# Create distributable package
npm run dist

# Build with bundled Python environment (recommended for distribution)
npm run build-with-python

# Create distributable package with bundled Python
npm run dist-with-python
```

### Python Environment Bundling

The IMPETUS Electron app can bundle the Python server environment for distribution:

```bash
# Create Python bundle
npm run bundle-python

# Test the Python bundle
npm run test-bundle

# Build with Python bundle included
npm run build-with-python
```

**What gets bundled:**
- Complete Python virtual environment with all dependencies
- IMPETUS server source code
- Platform-specific launcher scripts
- Automatic fallback to development environment

**Benefits:**
- One-click installation for end users
- No need to install Python or dependencies separately
- Consistent environment across different systems
- Portable and self-contained distribution

### Debugging

- Main process: Add `console.log()` statements
- Renderer process: Use Chrome DevTools (enabled in development)
- IPC communication: Monitor through Electron DevTools

## Configuration

The app uses `electron-store` for persistent settings:

- **Server Host/Port**: Configurable connection settings
- **Auto-start**: Option to start server on app launch
- **Notifications**: Toggle for system notifications

## Native Integration

### macOS Features

- **Menu Bar Icon**: Native tray icon with status indication
- **Notifications**: Native macOS notification center
- **Dock Integration**: Hidden dock icon for menubar-only experience
- **System Appearance**: Respects light/dark mode preferences

### Security

- **Context Isolation**: Enabled for security
- **Node Integration**: Disabled in renderer
- **Preload Script**: Secure API exposure
- **CSP**: Content Security Policy for web security

## Troubleshooting

### Common Issues

1. **Server won't start:**
   - Check Python virtual environment is activated
   - Verify IMPETUS server dependencies are installed
   - Check port 8080 is not in use

2. **Models not loading:**
   - Ensure server is running
   - Check model configuration files
   - Verify model file paths

3. **App won't build:**
   - Clear node_modules and reinstall
   - Check Electron version compatibility
   - Verify build dependencies

### Logs

Application logs are available:
- **Main process**: Console output during development
- **Renderer process**: Chrome DevTools console
- **Server logs**: IMPETUS server log files

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test on macOS
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Credits

Built with:
- [Electron](https://electronjs.org/) - Desktop app framework
- [electron-store](https://github.com/sindresorhus/electron-store) - Persistent storage
- Apple Human Interface Guidelines for design principles