#!/bin/bash

# ChatGPT History Converter
# Converts ChatGPT conversation exports to organized markdown files

set -e  # Exit on error

echo "==================================="
echo "ChatGPT History Converter"
echo "==================================="
echo ""

# If no arguments provided, show help
if [ $# -eq 0 ]; then
    echo "This tool converts your ChatGPT conversation export into organized markdown files."
    echo ""
    echo "What it does:"
    echo "  • Organizes conversations by date (year/month/day folders)"
    echo "  • Extracts markdown content into .md files with contextual titles"
    echo "  • Generates keyword hashtags using TF-IDF analysis"
    echo "  • Extracts code blocks into separate files"
    echo "  • Creates searchable JSON index files"
    echo ""
    echo "Usage:"
    echo "  ./convert_chatgpt_history.sh <output_directory>"
    echo ""
    echo "Example:"
    echo "  ./convert_chatgpt_history.sh chatgpt_history"
    echo "  ./convert_chatgpt_history.sh my_chatgpt_archive"
    echo ""
    echo "Before running, ensure you have extracted your ChatGPT export"
    echo "and placed conversations.json in the input/ directory."
    echo ""
    exit 0
fi

OUTPUT_DIR="$1"

# Check if required JSON file exists in input directory
if [ ! -f "input/conversations.json" ]; then
    echo "ERROR: ChatGPT conversations.json not found in input/ directory!"
    echo ""
    echo "Please extract your ChatGPT export and place the following file:"
    echo "  - input/conversations.json"
    echo ""
    echo "You can export your ChatGPT data from: https://chatgpt.com/gpts/mine (Data Controls)"
    exit 1
fi

# Show what will be processed
echo "Found export file:"
echo "  ✓ input/conversations.json ($(ls -lh input/conversations.json | awk '{print $5}'))"
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
echo "  3. Process your ChatGPT conversations.json from input/"
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
if [ ! -f "src/convert_chatgpt.py" ]; then
    echo "ERROR: src/convert_chatgpt.py not found!"
    echo "Please ensure the converter script is in the src/ directory."
    exit 1
fi

# Run the conversion
echo ""
echo "Starting conversion..."
echo "This may take a few minutes depending on the size of your history."
echo ""

python src/convert_chatgpt.py "input/conversations.json" "output/$OUTPUT_DIR"

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
echo "To use with Obsidian:"
echo "  1. Open Obsidian"
echo "  2. Click 'Open folder as vault'"
echo "  3. Select: output/$OUTPUT_DIR/"
echo ""
echo "Happy exploring your ChatGPT history!"
echo "==================================="