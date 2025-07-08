#!/bin/bash

# Claude History Converter
# A simple wrapper script to convert Claude conversation history to organized markdown files

set -e  # Exit on error

echo "==================================="
echo "Claude History Converter"
echo "==================================="
echo ""

# If no arguments provided, show help
if [ $# -eq 0 ]; then
    echo "This tool converts your Claude conversation export into organized markdown files."
    echo ""
    echo "What it does:"
    echo "  • Organizes conversations by date (year/month/day folders)"
    echo "  • Extracts markdown content into .md files with contextual titles"
    echo "  • Generates keyword hashtags using TF-IDF analysis"
    echo "  • Extracts code blocks into separate files"
    echo "  • Creates searchable JSON index files"
    echo ""
    echo "Usage:"
    echo "  ./convert_claude_history.sh <output_directory>"
    echo ""
    echo "Example:"
    echo "  ./convert_claude_history.sh claude_history"
    echo "  ./convert_claude_history.sh my_claude_archive"
    echo ""
    echo "Before running, ensure you have exported your Claude data files"
    echo "(conversations.json, projects.json, users.json) in this directory."
    echo ""
    exit 0
fi

OUTPUT_DIR="$1"

# Check if required JSON files exist in input directory
if [ ! -f "input/conversations.json" ] && [ ! -f "input/projects.json" ] && [ ! -f "input/users.json" ]; then
    echo "ERROR: No Claude export files found in input/ directory!"
    echo ""
    echo "Please place your exported Claude files in the input/ directory:"
    echo "  - input/conversations.json"
    echo "  - input/projects.json" 
    echo "  - input/users.json"
    echo ""
    echo "You can export your Claude data from: https://claude.ai/settings"
    exit 1
fi

# Show what will be processed
echo "Found export files:"
[ -f "input/conversations.json" ] && echo "  ✓ input/conversations.json ($(ls -lh input/conversations.json | awk '{print $5}'))"
[ -f "input/projects.json" ] && echo "  ✓ input/projects.json ($(ls -lh input/projects.json | awk '{print $5}'))"
[ -f "input/users.json" ] && echo "  ✓ input/users.json ($(ls -lh input/users.json | awk '{print $5}'))"
echo ""
echo "Output will be saved to: output/$OUTPUT_DIR/"
echo ""

# Check if output directory already exists
if [ -d "output/$OUTPUT_DIR" ]; then
    echo "WARNING: Output directory 'output/$OUTPUT_DIR' already exists!"
    echo "Running this script will DELETE the existing directory and create a new one."
    echo ""
fi

# Ask for confirmation before proceeding
echo "This will:"
echo "  1. Set up a Python virtual environment (if needed)"
echo "  2. Install required dependencies"
echo "  3. Process your Claude export files from input/"
echo "  4. Create organized markdown files in 'output/$OUTPUT_DIR/'"
echo ""
read -p "Do you want to proceed? (y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Conversion cancelled."
    exit 0
fi

# Remove existing directory if it exists
if [ -d "output/$OUTPUT_DIR" ]; then
    echo "Removing existing output directory..."
    rm -rf "output/$OUTPUT_DIR"
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
echo "Installing dependencies..."
source venv/bin/activate

# Install required packages
pip install --quiet --upgrade pip
pip install --quiet ijson scikit-learn nltk

# Download NLTK data
echo "Downloading language processing data..."
python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('punkt_tab', quiet=True); nltk.download('stopwords', quiet=True)" 2>/dev/null

# Check if converter script exists
if [ ! -f "src/convert_enhanced.py" ]; then
    echo "ERROR: src/convert_enhanced.py not found!"
    echo "Please ensure the converter script is in the src/ directory."
    exit 1
fi

# Change to src directory to run the converter
cd src

# Run the conversion with output directory
echo ""
echo "Starting conversion..."
echo "This may take a few minutes depending on the size of your history."
echo ""

python convert_enhanced.py "../output/$OUTPUT_DIR"

# Return to root directory
cd ..

echo ""
echo "==================================="
echo "Conversion complete!"
echo ""
echo "Your converted history is in: output/$OUTPUT_DIR/"
echo ""
echo "Features included:"
echo "  ✓ Conversations organized by date (year/month/day)"
echo "  ✓ Markdown files with full conversation context in titles"
echo "  ✓ Automatic keyword extraction and hashtags"
echo "  ✓ Code blocks extracted to separate files"
echo "  ✓ Searchable index files with keywords"
echo ""
echo "Happy exploring your Claude history!"
echo "====================================="