#!/usr/bin/env bash
set -e

echo "Building PhotoConverter for Linux..."

# pillow-heif requires libheif at runtime — install if missing
if ! ldconfig -p | grep -q libheif; then
    echo "libheif not found. Installing..."
    sudo apt-get install -y libheif-dev
fi

python3 -m PyInstaller \
    --onefile \
    --windowed \
    --name="PhotoConverter" \
    --clean \
    main.py

echo ""
echo "Build successful!"
echo "Binary: dist/PhotoConverter"
