#!/bin/bash
#
# Impetus LLM Server - Installation Redirect
# 
# This script redirects to the appropriate installer
#

echo "╔══════════════════════════════════════════════════════════╗"
echo "║          Impetus LLM Server - Choose Installer           ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo
echo "Please use one of the installers in the 'installers' directory:"
echo
echo "For Desktop Users (Recommended):"
echo "  cd installers && ./macos_simple_app.sh"
echo "  → Creates Impetus.app for distribution"
echo
echo "For Production Servers:"
echo "  cd installers && ./production_installer.sh"
echo "  → Sets up Gunicorn + nginx + system service"
echo
echo "For Docker:"
echo "  cd installers && ./docker_installer.sh"
echo "  → Creates Docker containers"
echo
echo "See installers/README.md for all options."
echo