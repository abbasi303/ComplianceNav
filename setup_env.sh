#!/bin/bash

echo "🏛️ =========================================="
echo "   ComplianceNavigator Environment Setup"
echo "   Unix/Linux/macOS Shell Script"
echo "🏛️ =========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo -e "${RED}❌ Python is not installed or not in PATH${NC}"
        echo "   Please install Python 3.10+ from https://python.org"
        echo "   Or use your system package manager:"
        echo "   - Ubuntu/Debian: sudo apt install python3 python3-venv python3-pip"
        echo "   - macOS: brew install python"
        echo "   - CentOS/RHEL: sudo yum install python3 python3-venv python3-pip"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

echo -e "${GREEN}✅ Python found:${NC}"
$PYTHON_CMD --version

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo -e "${RED}❌ Python 3.10+ is required${NC}"
    echo "   Current version: $PYTHON_VERSION"
    exit 1
fi

echo ""
echo -e "${BLUE}📦 Setting up virtual environment...${NC}"

# Remove existing venv if it exists
if [ -d "venv" ]; then
    echo "   Removing existing virtual environment..."
    rm -rf venv
fi

# Create virtual environment
$PYTHON_CMD -m venv venv
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to create virtual environment${NC}"
    echo "   Try installing python3-venv: sudo apt install python3-venv"
    exit 1
fi

echo -e "${GREEN}✅ Virtual environment created${NC}"

# Activate virtual environment
echo ""
echo -e "${BLUE}🔄 Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo ""
echo -e "${BLUE}⬆️ Upgrading pip...${NC}"
pip install --upgrade pip

# Install requirements
echo ""
echo -e "${BLUE}📦 Installing project dependencies...${NC}"
echo "   This may take a few minutes..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to install dependencies${NC}"
    echo "   Please check the error messages above"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ All dependencies installed successfully!${NC}"

# Set up environment file
echo ""
echo -e "${BLUE}⚙️ Setting up environment configuration...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env_template" ]; then
        cp .env_template .env
        echo -e "${GREEN}✅ Environment file (.env) created from template${NC}"
    else
        echo -e "${YELLOW}⚠️ .env_template not found, you'll need to create .env manually${NC}"
    fi
else
    echo -e "${GREEN}✅ Environment file (.env) already exists${NC}"
fi

# Create necessary directories
echo ""
echo -e "${BLUE}📁 Creating project directories...${NC}"
mkdir -p data/chroma_db
mkdir -p data/regulations
mkdir -p logs
echo -e "${GREEN}✅ Directories created${NC}"

# Make scripts executable
chmod +x setup_env.sh
if [ -f "main.py" ]; then
    chmod +x main.py
fi

# Display next steps
echo ""
echo -e "${GREEN}🎉 Setup Complete!${NC}"
echo ""
echo -e "${BLUE}📝 Next Steps:${NC}"
echo "   1. Edit .env file and add your GEMINI_API_KEY"
echo "   2. To run the application:"
echo "      - Activate environment: source venv/bin/activate"
echo "      - Start web app: python main.py"
echo "      - Or use CLI: python main.py cli"
echo ""
echo -e "${BLUE}🔑 Get your Gemini API key at:${NC}"
echo "   https://makersuite.google.com/app/apikey"
echo ""

# Ask if user wants to activate environment now
read -p "Do you want to activate the virtual environment now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}Virtual environment activated!${NC}"
    echo "You can now run: python main.py"
    exec bash --rcfile <(echo "source venv/bin/activate; PS1='(ComplianceNavigator) \u@\h:\w\$ '")
fi 