# Impetus Installer Toolkit

Preferred DMG builder:
- `create_dmg.sh` – customizable DMG builder

Deprecated/for reference only:
- `create_simple_dmg.sh` – older/simple builder
- Root-level `create_professional_dmg.sh` – kept for backwards compatibility

First‑run and launcher scripts:
- `scripts/launcher.sh`
- `scripts/first_run.py`

Assets:
- `assets/` – AppIcon.icns, dmg-background.png, Info.plist

To build a DMG:
```bash
./installers/create_dmg.sh
```
# Impetus LLM Server - Installers

This directory contains various installers for different deployment scenarios.

## Quick Start

For users who want a fully self-contained macOS app (no dependencies):
```bash
./macos_standalone_app.sh
```

This creates a standalone `Impetus.app` with Python and all dependencies included. Users don't need anything installed!

## Available Installers

### 1. macOS Standalone App (`macos_standalone_app.sh`) ⭐ RECOMMENDED
**Best for: End users who want it to "just work"**
- Creates a fully self-contained .app bundle
- Includes Python runtime and all dependencies
- No requirements on user's system
- ~250MB download but instant start
- Professional distribution-ready DMG

### 2. macOS Simple App (`macos_simple_app.sh`)
**Best for: Users who already have Python installed**
- Creates a standard .app bundle
- Generates .dmg for distribution  
- Auto-installs dependencies on first launch
- Requires: Python 3.11+ on user's system
- Smaller download (~50MB)

### 3. macOS GUI Installer (`macos_gui_installer.sh`)
**Best for: Creating a traditional .pkg installer**
- Creates a .pkg installer with installation wizard
- Includes pre/post install scripts
- Professional installation experience
- Note: Currently has issues with bundling dependencies

### 4. macOS App Bundle Builder (`macos_app_builder.sh`)
**Best for: Fully self-contained app (experimental)**
- Attempts to bundle Python runtime
- No dependencies required on user's system
- Larger file size
- More complex build process

### 5. Production Installer (`production_installer.sh`)
**Best for: Server deployments**
- Sets up Gunicorn + nginx
- Configures as system service
- Production-grade deployment
- For servers, not desktop users

### 6. Docker Installer (`docker_installer.sh`)
**Best for: Container deployments**
- Creates Docker images
- Sets up docker-compose
- Good for cloud deployments

### 7. Service Installer (`service_installer.sh`)
**Best for: Adding service integration**
- Adds systemd/launchd service
- For existing installations
- Auto-start on boot

### 8. Uninstaller (`uninstaller.sh`)
- Removes Impetus installations
- Supports all installation types
- Optional data preservation

### 9. Updater (`updater.sh`)
- Zero-downtime updates
- Automatic rollback on failure
- For existing installations

## Distribution Guide

### For Desktop Users

1. **Best Option**: Use `macos_standalone_app.sh` ⭐
   ```bash
   ./macos_standalone_app.sh
   # Creates Impetus-Standalone-1.0.0.dmg
   ```
   
   Users need:
   - macOS 13.0+ on Apple Silicon
   - Nothing else! Everything included!

2. **Smaller Download**: Use `macos_simple_app.sh`
   ```bash
   ./macos_simple_app.sh
   # Creates Impetus-1.0.0.dmg
   ```
   
   Users need:
   - macOS 13.0+ on Apple Silicon
   - Python 3.11+ (from python.org or Homebrew)

3. **Traditional Installer**: Use `macos_gui_installer.sh`
   ```bash
   ./macos_gui_installer.sh
   # Creates Impetus-LLM-Server-1.0.0.pkg
   ```

### For Servers

Use `production_installer.sh` for a full production setup:
```bash
./production_installer.sh
```

### For Containers

Use `docker_installer.sh`:
```bash
./docker_installer.sh
```

## Signing and Notarization

For distribution outside your organization:

1. **Code Signing**: Get a Developer ID certificate from Apple
2. **Notarization**: Required for Gatekeeper on macOS 10.15+

Without signing, users must right-click and select "Open" to bypass Gatekeeper.

## Troubleshooting

### App won't open
- Check if Python 3.11+ is installed
- Right-click and select "Open" if unsigned
- Check Console.app for error messages

### Dependencies fail to install
- Ensure good internet connection
- Check available disk space
- Try running from Terminal to see errors

### Server won't start
- Check if port 8080 is already in use
- Look at ~/Library/Application Support/Impetus/impetus.log
- Ensure Apple Silicon Mac (M1/M2/M3/M4)

## Development Notes

The installers follow this philosophy:
- **Simple > Complex**: Start with the simple app for most users
- **Progressive Enhancement**: Users can install Python when ready
- **No Surprises**: Clear requirements and error messages
- **User Control**: Apps don't auto-install without permission