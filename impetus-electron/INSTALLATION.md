# IMPETUS Installation Guide

## 🎉 Your IMPETUS App is Ready!

The IMPETUS.app has been successfully built and is ready to install in your Applications folder.

## 📦 App Location

Your built application is located at:
```
dist/mac-arm64/IMPETUS.app
```

## 🚀 Installation Steps

### Option 1: Command Line Installation
```bash
# Copy to Applications folder
cp -r dist/mac-arm64/IMPETUS.app /Applications/

# Or if you prefer a symbolic link
ln -s "$(pwd)/dist/mac-arm64/IMPETUS.app" /Applications/
```

### Option 2: Manual Installation
1. Open Finder
2. Navigate to the `impetus-electron/dist/mac-arm64/` folder
3. Drag `IMPETUS.app` to your Applications folder

## 🔐 First Launch Security

On first launch, macOS may show a security warning because the app isn't code-signed. To open it:

1. **Method 1**: Right-click on IMPETUS.app and select "Open"
2. **Method 2**: Go to System Settings > Privacy & Security and click "Open Anyway"
3. **Method 3**: Run in Terminal: `xattr -cr /Applications/IMPETUS.app`

## 📋 Requirements

- macOS 12.0 or later (optimized for Apple Silicon)
- Python 3.11+ installed on your system (for now)
- The IMPETUS server repository accessible

## 🎯 Using IMPETUS

1. **Launch**: Double-click IMPETUS in Applications or click the menubar icon
2. **Start Server**: Click "Start Server" in the menubar or main window
3. **Configure VS Code**: 
   - Set API endpoint to: `http://localhost:8080`
   - Use with Cline, Continue.dev, or other OpenAI-compatible extensions
4. **Load Models**: Place model files in the configured models directory
5. **Switch Models**: Use the menubar to switch between loaded models

## ⚡ Quick Start

After installation:
```bash
# 1. Launch IMPETUS from Applications
# 2. Click the rocket icon in your menubar
# 3. Select "Start Server"
# 4. Open VS Code and start using Cline!
```

## 🛠️ Troubleshooting

### App Won't Open
- Right-click and select "Open" to bypass Gatekeeper
- Or run: `xattr -cr /Applications/IMPETUS.app`

### Server Won't Start
- Ensure Python 3.11+ is installed: `python3 --version`
- Check if port 8080 is available: `lsof -i :8080`
- View logs in the IMPETUS main window

### Models Not Loading
- Check model file formats (GGUF, SafeTensors, MLX, etc.)
- Ensure models are in the correct directory
- Verify file permissions

## 📝 Notes

- This is a development build without code signing
- For production deployment, consider code signing and notarization
- The app currently requires Python installed on the system
- Future versions will include bundled Python for zero dependencies

## 🚀 Next Steps

1. Install the app in Applications
2. Configure your model directory
3. Start using IMPETUS with VS Code and Cline
4. Enjoy local, private AI coding assistance!

---

Built with ❤️ by IMPETUS - Intelligent Model Platform Enabling Taskbar Unified Server