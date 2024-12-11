#!/bin/bash

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored status messages
print_status() {
    echo -e "${GREEN}[✓] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[!] $1${NC}"
}

print_error() {
    echo -e "${RED}[✗] $1${NC}"
}

# Print welcome message
echo "======================================================"
echo "    Atlas SkillTech Placement Assistant Setup"
echo "======================================================"

# Check Python installation
print_status "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if studbud virtual environment exists
if [ ! -d "studbud" ]; then
    print_warning "Virtual environment 'studbud' not found."
    exit 1
fi

# Activate studbud virtual environment
print_status "Activating studbud virtual environment..."
source studbud/bin/activate || {
    print_error "Failed to activate virtual environment"
    exit 1
}

# Install/Upgrade pip
print_status "Upgrading pip..."
python -m pip install --upgrade pip

# Install requirements
print_status "Installing dependencies..."
pip install -r requirements.txt || {
    print_error "Failed to install dependencies"
    exit 1
}

# Check Ollama installation
print_status "Checking Ollama installation..."
if ! command -v ollama &> /dev/null; then
    print_error "Ollama is not installed. Please install Ollama first."
    echo "Visit: https://ollama.ai/download"
    exit 1
fi

# Check if Ollama is running
print_status "Checking if Ollama is running..."
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    print_warning "Ollama service is not running. Starting Ollama..."
    ollama serve &
    sleep 5  # Wait for Ollama to start
fi

# Check and pull Gemma model
print_status "Checking Gemma 27B model..."
if ! ollama list | grep -q "gemma:27b"; then
    print_warning "Gemma 27B model not found. Pulling model..."
    ollama pull gemma:27b || {
        print_error "Failed to pull Gemma 27B model"
        exit 1
    }
fi

# Create necessary directories
print_status "Creating required directories..."
mkdir -p data/backups data/cache static/images

# Check environment file
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Creating from template..."
    cp .env.example .env || {
        print_error "Failed to create .env file"
        exit 1
    }
fi

# Run initialization checks
print_status "Running initialization checks..."
python init_setup.py || {
    print_error "Initialization failed"
    exit 1
}

# Start the application
print_status "Starting Streamlit application..."
echo "======================================================"
streamlit run app.py

# Cleanup on exit
trap 'echo "Cleaning up..."; deactivate' EXIT