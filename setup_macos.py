#!/usr/bin/env python3
"""
macOS Application Setup Script for GerdsenAI MLX Manager
Creates proper .app bundle with menu bar integration
"""

from setuptools import setup, find_packages
import os
import sys
from pathlib import Path

# Check if we're on macOS
if sys.platform != 'darwin':
    print("This setup script is for macOS only")
    sys.exit(1)

# Try to import py2app
try:
    import py2app
    PY2APP_AVAILABLE = True
except ImportError:
    PY2APP_AVAILABLE = False
    print("py2app not available - install with: pip install py2app")

APP_NAME = "GerdsenAI MLX Manager"
APP_VERSION = "2.0.0"
APP_IDENTIFIER = "com.gerdsen.ai.mlx.manager"

# Application entry point
APP = ['src/macos_service.py']

# Data files to include in the bundle
DATA_FILES = [
    ('gerdsen_ai_server', ['gerdsen_ai_server']),
    ('ui', ['ui']),
    ('assets', ['assets']),
]

# Options for py2app
OPTIONS = {
    'py2app': {
        'app': APP,
        'data_files': DATA_FILES,
        'options': {
            'argv_emulation': True,
            'iconfile': 'assets/icon.icns',  # You would need to create this
            'plist': {
                'CFBundleName': APP_NAME,
                'CFBundleDisplayName': APP_NAME,
                'CFBundleIdentifier': APP_IDENTIFIER,
                'CFBundleVersion': APP_VERSION,
                'CFBundleShortVersionString': APP_VERSION,
                'LSUIElement': True,  # Run as background app (no dock icon)
                'NSHighResolutionCapable': True,
                'NSRequiresAquaSystemAppearance': False,  # Support dark mode
                'LSMinimumSystemVersion': '12.0',  # macOS Monterey minimum
                'NSHumanReadableCopyright': 'Copyright © 2025 GerdsenAI',
                'CFBundleDocumentTypes': [],
                'LSApplicationCategoryType': 'public.app-category.developer-tools',
                'NSAppleEventsUsageDescription': 'This app uses Apple Events for system integration.',
                'NSSystemAdministrationUsageDescription': 'This app needs admin access for system monitoring.',
            },
            'packages': [
                'flask',
                'flask_socketio',
                'flask_cors',
                'psutil',
                'rumps',
                'pystray',
                'PIL',
                'numpy',
                'pandas',
                'requests',
                'websockets',
                'aiohttp',
            ],
            'includes': [
                'src.macos_service',
                'src.apple_silicon_detector',
                'src.enhanced_mlx_manager',
                'gerdsen_ai_server.src.main',
            ],
            'excludes': [
                'tkinter',
                'matplotlib',
                'scipy',
                'IPython',
                'jupyter',
            ],
            'resources': [
                'gerdsen_ai_server/src/static',
                'ui',
                'assets',
            ],
            'frameworks': [],
            'dylib_excludes': [],
            'optimize': 2,
        }
    }
}

def create_app_icon():
    """Create application icon if it doesn't exist"""
    icon_path = Path('assets/icon.icns')
    
    if not icon_path.exists():
        print("Creating placeholder icon...")
        # You would normally create a proper .icns file here
        # For now, we'll just create the directory
        icon_path.parent.mkdir(exist_ok=True)
        
        # Create a simple placeholder
        try:
            from PIL import Image
            
            # Create a simple blue icon
            img = Image.new('RGB', (512, 512), color='#007AFF')
            
            # Save as PNG first (you'd convert to .icns with iconutil)
            png_path = icon_path.with_suffix('.png')
            img.save(png_path)
            
            print(f"Created placeholder icon: {png_path}")
            print("Note: Convert to .icns format for production use")
            
        except ImportError:
            print("PIL not available - skipping icon creation")

def create_info_plist():
    """Create Info.plist template"""
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>{APP_NAME}</string>
    <key>CFBundleDisplayName</key>
    <string>{APP_NAME}</string>
    <key>CFBundleIdentifier</key>
    <string>{APP_IDENTIFIER}</string>
    <key>CFBundleVersion</key>
    <string>{APP_VERSION}</string>
    <key>CFBundleShortVersionString</key>
    <string>{APP_VERSION}</string>
    <key>CFBundleExecutable</key>
    <string>GerdsenAI MLX Manager</string>
    <key>CFBundleIconFile</key>
    <string>icon.icns</string>
    <key>LSUIElement</key>
    <true/>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSRequiresAquaSystemAppearance</key>
    <false/>
    <key>LSMinimumSystemVersion</key>
    <string>12.0</string>
    <key>NSHumanReadableCopyright</key>
    <string>Copyright © 2025 GerdsenAI</string>
    <key>LSApplicationCategoryType</key>
    <string>public.app-category.developer-tools</string>
    <key>NSAppleEventsUsageDescription</key>
    <string>This app uses Apple Events for system integration.</string>
    <key>NSSystemAdministrationUsageDescription</key>
    <string>This app needs admin access for system monitoring.</string>
</dict>
</plist>"""
    
    with open('Info.plist', 'w') as f:
        f.write(plist_content)
    
    print("Created Info.plist template")

def main():
    """Main setup function"""
    print(f"Setting up {APP_NAME} for macOS...")
    
    # Create necessary files
    create_app_icon()
    create_info_plist()
    
    if PY2APP_AVAILABLE:
        # Run py2app setup
        setup(
            app=APP,
            data_files=DATA_FILES,
            options=OPTIONS['py2app']['options'],
            setup_requires=['py2app'],
            install_requires=[
                'flask>=3.1.1',
                'flask-socketio>=5.4.1',
                'flask-cors>=5.0.0',
                'psutil>=6.1.0',
                'rumps>=0.4.0',
                'pystray>=0.19.5',
                'Pillow>=11.0.0',
                'requests>=2.32.3',
                'numpy>=2.2.1',
                'pandas>=2.2.3',
            ],
        )
    else:
        # Fallback setup without py2app
        setup(
            name=APP_NAME,
            version=APP_VERSION,
            description="Advanced MLX model management for Apple Silicon",
            author="GerdsenAI",
            packages=find_packages(),
            install_requires=[
                'flask>=3.1.1',
                'flask-socketio>=5.4.1',
                'flask-cors>=5.0.0',
                'psutil>=6.1.0',
                'rumps>=0.4.0',
                'pystray>=0.19.5',
                'Pillow>=11.0.0',
                'requests>=2.32.3',
                'numpy>=2.2.1',
                'pandas>=2.2.3',
            ],
            entry_points={
                'console_scripts': [
                    'gerdsen-ai-mlx=src.macos_service:main',
                ],
            },
            classifiers=[
                'Development Status :: 4 - Beta',
                'Intended Audience :: Developers',
                'License :: OSI Approved :: MIT License',
                'Programming Language :: Python :: 3.11',
                'Operating System :: MacOS :: MacOS X',
            ],
            python_requires='>=3.11',
        )

if __name__ == '__main__':
    main()

