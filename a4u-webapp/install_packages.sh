#!/bin/bash

echo "=================================================="
echo " a4u-webapp: Installing Python dependencies..."
echo "=================================================="

# Check for python3
if ! command -v python3 &> /dev/null
then
    echo "python3 could not be found. Please install Python 3."
    exit
fi

# Create and activate virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing packages from requirements.txt..."
pip install -r requirements.txt

echo ""
echo "=================================================="
echo " Installation complete!"
echo " Run 'python run.py' to start the application."
echo "=================================================="