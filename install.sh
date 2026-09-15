#!/bin/bash
# NetReaper Installer - by 09azo14 | MIT License
set -e

echo "============================================"
echo "  NetReaper v1.0.0 - Installer"
echo "  Author: 09azo14 | License: MIT"
echo "============================================"

# Check Python 3.8+
python3 --version >/dev/null 2>&1 || { echo "Python 3 required!"; exit 1; }

# Create a project-local virtual environment if missing
VENV_DIR=".venv"
if [ ! -x "$VENV_DIR/bin/python" ]; then
    echo "Creating virtual environment at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi

VENV_PYTHON="$VENV_DIR/bin/python"

# Install Python dependencies into the virtual environment
"$VENV_PYTHON" -m pip install -r requirements.txt --quiet

# Create necessary directories
mkdir -p reports logs wordlists

# Download basic wordlists if missing
if [ ! -f wordlists/router_defaults.txt ]; then
    echo "Creating basic wordlists..."
    cat > wordlists/router_defaults.txt << 'EOF'
admin
password
123456
root
test
admin123
router
guest
user
1234
adminadmin
password123
root123
support
changeme
default
EOF
fi

# Make executable
chmod +x netreaper.py

echo ""
echo " NetReaper installed! Run with: $VENV_PYTHON netreaper.py"
echo "  or: ./netreaper.py"
