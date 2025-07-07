# Python Environment Bundling Guide

This guide explains how to bundle the Python environment with the IMPETUS Electron app for distribution.

## Overview

The Python bundling system creates a self-contained Python environment that can be distributed with the Electron app, eliminating the need for users to install Python or dependencies separately.

## Quick Start

```bash
# Bundle Python environment and create distributable
npm run dist-with-python
```

This single command will:
1. Create a portable Python environment
2. Install all dependencies
3. Copy the IMPETUS server source code
4. Test the bundle
5. Build the Electron app with the bundle included

## Step-by-Step Process

### 1. Create Python Bundle

```bash
npm run bundle-python
```

**What this does:**
- Creates a virtual environment in `resources/python-bundle/venv/`
- Installs all dependencies from `requirements_production.txt`
- Copies the IMPETUS server source code
- Creates platform-specific launcher scripts
- Generates bundle metadata

**Bundle structure:**
```
resources/python-bundle/
├── venv/                     # Python virtual environment
│   ├── bin/python           # Python executable (Unix)
│   ├── Scripts/python.exe   # Python executable (Windows)
│   └── lib/                 # Python libraries
├── src/                     # IMPETUS server source code
│   ├── production_main.py   # Main server script
│   └── ...                  # Other server modules
├── start-server.sh          # Unix launcher script
├── start-server.bat         # Windows launcher script
├── requirements_production.txt
├── bundle-info.json         # Bundle metadata
└── README.md               # Bundle documentation
```

### 2. Test the Bundle

```bash
npm run test-bundle
```

**What this tests:**
- Bundle structure integrity
- Python executable functionality
- Dependency imports
- Server startup process

### 3. Build with Bundle

```bash
npm run build-with-python
```

This creates a development build with the Python bundle included.

### 4. Create Distributable

```bash
npm run dist-with-python
```

This creates a distributable package (DMG on macOS, installer on Windows) with the Python bundle embedded.

## How It Works

### Development vs Production

**Development Mode:**
- Looks for bundled Python first
- Falls back to development venv (`../venv/`)
- Falls back to system Python

**Production Mode:**
- Uses bundled Python from `Resources/python-bundle/`
- Runs server from bundled source code
- Self-contained and portable

### Path Resolution

The Electron app automatically detects the environment and uses the appropriate paths:

```javascript
getBundledPythonPath() {
    if (app.isPackaged) {
        // Production: Resources/python-bundle/venv/bin/python
        return path.join(process.resourcesPath, 'python-bundle', 'venv', 'bin', 'python');
    } else {
        // Development: resources/python-bundle/venv/bin/python
        return path.join(__dirname, '..', 'resources', 'python-bundle', 'venv', 'bin', 'python');
    }
}
```

## Platform Support

### macOS
- Uses `venv/bin/python` executable
- Creates `.sh` launcher script
- Bundles in `Resources/python-bundle/` in the app bundle

### Windows
- Uses `venv/Scripts/python.exe` executable
- Creates `.bat` launcher script
- Bundles in `Resources/python-bundle/` in the installation directory

### Linux
- Uses `venv/bin/python` executable
- Creates `.sh` launcher script
- Bundles in `Resources/python-bundle/` in the app directory

## Configuration

### Environment Variables

The bundled server runs with these environment variables:

```bash
PYTHONPATH=<bundle-src-directory>
IMPETUS_BUNDLED=true
```

### Bundle Metadata

The `bundle-info.json` file contains:

```json
{
  "name": "IMPETUS Python Bundle",
  "version": "1.0.0",
  "platform": "darwin-arm64",
  "created": "2025-01-01T00:00:00.000Z",
  "python_version": "Python 3.11.0",
  "dependencies": ["flask==2.3.2", "mlx==0.4.0", ...]
}
```

## Troubleshooting

### Bundle Creation Issues

**"Virtual environment creation failed"**
- Ensure Python 3.11+ is installed
- Check if `python3 -m venv` works
- Verify write permissions in the project directory

**"Requirements installation failed"**
- Check that `requirements_production.txt` exists
- Verify internet connection for package downloads
- Ensure sufficient disk space

### Runtime Issues

**"Python executable not found"**
- Verify the bundle was created successfully
- Check if the bundle directory exists in the built app
- Ensure the Python executable has proper permissions

**"Server startup failed"**
- Check the bundle test output for errors
- Verify all dependencies are installed correctly
- Check the server logs for specific error messages

### Testing the Bundle

Run the test suite to verify bundle integrity:

```bash
npm run test-bundle
```

**Common test failures:**

1. **Bundle structure test fails**
   - Re-run `npm run bundle-python`
   - Check for file permission issues

2. **Python executable test fails**
   - Python installation might be corrupted
   - Try recreating the bundle

3. **Dependencies test fails**
   - Check internet connection during bundling
   - Verify all packages installed correctly

4. **Server startup test fails**
   - Check for port conflicts
   - Verify server configuration

## Distribution Notes

### File Size

The Python bundle significantly increases the app size:
- Base Electron app: ~100MB
- With Python bundle: ~500MB-1GB (depending on dependencies)

### Performance

- First startup may be slower due to Python initialization
- Runtime performance is identical to development mode
- Bundle decompression happens automatically

### Security

- Bundle is self-contained and isolated
- No system Python dependencies
- All packages are pinned to specific versions
- Bundle integrity is verified at startup

## Best Practices

1. **Always test the bundle** before distribution
2. **Keep dependencies minimal** to reduce bundle size
3. **Pin dependency versions** in requirements.txt
4. **Test on target platforms** before release
5. **Include bundle metadata** for debugging

## Command Reference

```bash
# Bundle management
npm run bundle-python     # Create Python bundle
npm run test-bundle      # Test bundle integrity

# Development builds
npm run build-with-python # Build with bundle
npm run dev              # Development mode (no bundle needed)

# Distribution
npm run dist-with-python # Create distributable with bundle
npm run dist             # Create distributable without bundle

# Individual steps
npm run bundle-python && npm run test-bundle && npm run build
```

## File Structure After Bundling

```
impetus-electron/
├── resources/
│   └── python-bundle/        # Created by bundling
│       ├── venv/            # Virtual environment
│       ├── src/             # Server source code
│       ├── start-server.sh  # Launcher script
│       └── bundle-info.json # Metadata
├── dist/                    # Built application
│   └── IMPETUS.app/         # macOS app bundle
│       └── Contents/
│           └── Resources/
│               └── python-bundle/  # Bundled Python
└── scripts/
    ├── bundle-python.js     # Bundling script
    └── test-bundle.js       # Testing script
```

This bundling system ensures that IMPETUS can be distributed as a complete, self-contained application that works out of the box on any compatible system.