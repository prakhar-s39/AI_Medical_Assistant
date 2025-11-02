#!/bin/bash
# Verification script to check if everything is set up correctly

echo "🔍 Verifying AI Medical Assistant Setup..."
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python
echo "1. Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✅ Python found: $PYTHON_VERSION${NC}"
else
    echo -e "${RED}❌ Python3 not found${NC}"
    exit 1
fi

# Check Ollama
echo ""
echo "2. Checking Ollama..."
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✅ Ollama is installed${NC}"
    
    # Check if Ollama service is running
    if systemctl is-active --quiet ollama 2>/dev/null || pgrep -x ollama > /dev/null; then
        echo -e "${GREEN}✅ Ollama service is running${NC}"
    else
        echo -e "${YELLOW}⚠️  Ollama service may not be running${NC}"
        echo "   Try: systemctl start ollama"
    fi
    
    # Check for phi3:mini model
    echo "   Checking for phi3:mini model..."
    MODELS=$(ollama list 2>/dev/null)
    if echo "$MODELS" | grep -q "phi3:mini"; then
        echo -e "${GREEN}✅ phi3:mini model is available${NC}"
    else
        echo -e "${YELLOW}⚠️  phi3:mini model not found${NC}"
        echo "   Run: ollama pull phi3:mini"
    fi
else
    echo -e "${RED}❌ Ollama not found${NC}"
    echo "   Install from: https://ollama.ai/download"
    exit 1
fi

# Check Python dependencies
echo ""
echo "3. Checking Python dependencies..."
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "   Using virtual environment"
fi

REQUIRED_PACKAGES=("fastapi" "uvicorn" "ollama" "pydantic")
MISSING_PACKAGES=()

for package in "${REQUIRED_PACKAGES[@]}"; do
    if python3 -c "import ${package}" 2>/dev/null; then
        echo -e "${GREEN}✅ $package is installed${NC}"
    else
        echo -e "${RED}❌ $package is missing${NC}"
        MISSING_PACKAGES+=("$package")
    fi
done

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}⚠️  Missing packages. Install with:${NC}"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Check frontend files
echo ""
echo "4. Checking frontend files..."
FRONTEND_FILES=("frontend/index.html" "frontend/styles.css" "frontend/script.js")
for file in "${FRONTEND_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $(basename $file) exists${NC}"
    else
        echo -e "${RED}❌ $(basename $file) not found${NC}"
    fi
done

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Setup Summary:"
echo ""

if [ ${#MISSING_PACKAGES[@]} -eq 0 ] && command -v ollama &> /dev/null && [ -f "frontend/index.html" ]; then
    echo -e "${GREEN}✅ All checks passed!${NC}"
    echo ""
    echo "🚀 To start the server:"
    echo "   ./start_server.sh"
    echo ""
    echo "🌐 Then access from your laptop:"
    echo "   http://$(hostname -I | awk '{print $1}'):8000"
else
    echo -e "${YELLOW}⚠️  Some issues found. Please fix them before running the server.${NC}"
fi

echo ""

