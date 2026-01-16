#!/bin/bash
# Build a standalone macOS .app bundle for Mosaic
# This allows notifications to show as "Mosaic" instead of "Python"

set -e

echo "Building Mosaic.app for macOS..."
echo

# Check if PyInstaller is installed
if ! uv run python -c "import PyInstaller" 2>/dev/null; then
    echo "Installing PyInstaller..."
    uv pip install pyinstaller
fi

# Create a simple entry point for the app
cat > /tmp/mosaic_entry.py << 'EOF'
"""Mosaic macOS app entry point."""
import sys
from mosaic.server import main

if __name__ == "__main__":
    sys.exit(main())
EOF

# Build the .app bundle
uv run pyinstaller \
    --name=Mosaic \
    --onefile \
    --windowed \
    --osx-bundle-identifier=com.mosaic.app \
    --icon=assets/icon.icns \
    /tmp/mosaic_entry.py

# Sign the bundle
echo
echo "Signing Mosaic.app..."
codesign -s - dist/Mosaic.app

# Verify signature
echo
echo "Verifying signature..."
codesign -dv dist/Mosaic.app

echo
echo "✅ Build complete: dist/Mosaic.app"
echo
echo "To install:"
echo "  cp -r dist/Mosaic.app /Applications/"
echo
echo "Notifications will now show as 'Mosaic' instead of 'Python'"
