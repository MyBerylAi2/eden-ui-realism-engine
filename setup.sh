#!/bin/bash

# EDEN UI REALISM ENGINE - Setup Script
# =====================================

set -e

echo "🌿 EDEN UI REALISM ENGINE - Setup"
echo "=================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}Setting up backend...${NC}"
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install PyTorch with CUDA support
echo "Installing PyTorch (CUDA 12.1)..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install other dependencies
echo "Installing backend dependencies..."
pip install -r requirements.txt

echo -e "${GREEN}✓ Backend setup complete!${NC}"

cd ..

echo -e "${BLUE}Setting up frontend...${NC}"
cd frontend

# Install Node.js dependencies
echo "Installing npm packages..."
npm install

echo -e "${GREEN}✓ Frontend setup complete!${NC}"

cd ..

# Create necessary directories
echo "Creating directories..."
mkdir -p models outputs uploads comfy-workflows

echo ""
echo -e "${GREEN}==================================${NC}"
echo -e "${GREEN}Setup complete!${NC}"
echo ""
echo "To start EDEN UI:"
echo ""
echo "1. Start the backend:"
echo "   cd backend && source venv/bin/activate && python main.py"
echo ""
echo "2. In a new terminal, start the frontend:"
echo "   cd frontend && npm start"
echo ""
echo "3. Open http://localhost:3000 in your browser"
echo ""
echo "Optional: Set up environment variables in backend/.env"
echo "   HF_TOKEN=your_huggingface_token"
echo "   OPENAI_API_KEY=your_openai_key (optional)"
echo ""
