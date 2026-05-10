#!/bin/bash
# Auto-setup script untuk Kiro Token Generator

set -e

echo "=========================================="
echo "  Kiro Token Generator - Auto Setup"
echo "=========================================="
echo ""

# Check Python version
echo "[1/4] Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python 3.10+ required. Current: $PYTHON_VERSION"
    exit 1
fi
echo "✓ Python $PYTHON_VERSION detected"

# Install dependencies
echo ""
echo "[2/4] Installing dependencies..."
pip3 install -q camoufox browserforge aiohttp
echo "✓ Dependencies installed"

# Check accounts.txt
echo ""
echo "[3/4] Checking accounts.txt..."
if [ ! -f "accounts.txt" ]; then
    echo "❌ accounts.txt not found!"
    echo ""
    echo "Create accounts.txt with format:"
    echo "email1@gmail.com:password1"
    echo "email2@gmail.com:password2"
    exit 1
fi

ACCOUNT_COUNT=$(wc -l < accounts.txt)
echo "✓ Found $ACCOUNT_COUNT accounts"

# Ready to run
echo ""
echo "[4/4] Setup complete!"
echo ""
echo "=========================================="
echo "  Ready to Generate Tokens"
echo "=========================================="
echo ""
echo "Run script:"
echo "  nohup python3 kiro_token_generator.py > kiro.log 2>&1 &"
echo ""
echo "Monitor progress:"
echo "  tail -f kiro.log"
echo ""
echo "Check count:"
echo "  python3 -c \"import json; print(f'{len(json.load(open(\\\"kiro_tokens.json\\\")))}/$ACCOUNT_COUNT')\""
echo ""
