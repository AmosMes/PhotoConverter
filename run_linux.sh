#!/usr/bin/env bash
set -e

echo "Starting PhotoConverter..."

if ! command -v python3 &>/dev/null; then
    echo "Python 3 not found. Install Python 3.11+ and try again." >&2
    exit 1
fi

# pillow-heif requires libheif at runtime
if ! ldconfig -p 2>/dev/null | grep -q libheif; then
    echo "libheif not found. Installing..."
    sudo apt-get install -y libheif-dev
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -m pip install -q -r "$SCRIPT_DIR/requirements.txt"
python3 "$SCRIPT_DIR/main.py"
