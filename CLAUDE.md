# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Core Development Philosophy

This project emphasizes systematic problem-solving through:
1. **Socratic Method**: Question assumptions and seek evidence before implementing
2. **OODA Loop**: Observe → Orient → Decide → Act in iterative cycles
3. **Evidence-Based Decisions**: Measure, don't guess - especially for performance

## Project Overview

Impetus-LLM-Server is a **production-ready** local LLM server optimized for Apple Silicon. The project provides both a standalone macOS app for end users and a full development environment for contributors.

### Status: v1.0.0 - Distribution Ready ✅
The project now features:
- ✅ **Standalone macOS App**: Self-contained .app with embedded Python runtime
- ✅ **Zero-dependency Installation**: Users just download and run
- ✅ **Production Server**: Gunicorn with Apple Silicon optimization
- ✅ **Beautiful Dashboard**: React/Three.js frontend
- ✅ **OpenAI API Compatibility**: Works with all major AI tools
- ✅ **Comprehensive Installers**: Multiple distribution options
- ✅ **Enterprise Features**: Health checks, monitoring, API docs

## CI/CD Pipeline

### CI/CD Strategies
- Implemented GitHub Actions for automated testing and deployment
- Comprehensive test suite runs on every pull request
- Automated standalone app build and distribution process
- Performance and security checks integrated into pipeline
- Automatic version bumping and release creation
- Cross-platform compatibility testing on multiple Mac configurations

## Building for Distribution

### Creating the Standalone App (Recommended)
```bash
cd installers
./macos_standalone_app.sh
# Creates Impetus-Standalone-1.0.0.dmg with embedded Python
```

This creates a fully self-contained app that users can download and run without any dependencies.

[... rest of the existing file content remains unchanged ...]