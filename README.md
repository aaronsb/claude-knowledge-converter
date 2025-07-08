# Claude History Converter

Convert your Claude conversation history into an organized, searchable collection of markdown files.

![Obsidian Graph View of Claude Conversations](claude-data-graph.png)

## Features

- 📁 **Organized Structure** - Conversations organized by date (year/month/day)
- 📝 **Markdown Extraction** - Automatically detects and extracts markdown content
- 🏷️ **Smart Hashtags** - Uses TF-IDF analysis to generate relevant keyword hashtags
- 💻 **Code Extraction** - Code blocks saved as separate files with proper extensions
- 🔍 **Searchable Index** - JSON index files with keywords for easy discovery
- 📖 **Context-Rich Titles** - Each markdown file includes full conversation context

## Quick Start

1. **Export your Claude data**
   - Go to https://claude.ai/settings
   - Download your data (you'll get `conversations.json`, `projects.json`, and `users.json`)

2. **Clone this repository**
   ```bash
   git clone https://github.com/aaronsb/claude-knowledge-converter.git
   cd claude-knowledge-converter
   ```

3. **Copy your Claude export files to the input directory**
   ```bash
   cp ~/Downloads/conversations.json input/
   cp ~/Downloads/projects.json input/
   cp ~/Downloads/users.json input/
   ```

4. **Run the converter**
   ```bash
   # Show help and usage information
   ./convert_claude_history.sh
   
   # Convert with default directory name
   ./convert_claude_history.sh claude_history
   
   # Convert with custom directory name
   ./convert_claude_history.sh my_claude_archive
   ```

That's it! Your converted history will be in the `output/claude_history/` directory (or `output/your_custom_name/` if you specify one).

## Project Structure

```
claude-knowledge-converter/
├── convert_claude_history.sh    # Main conversion script
├── README.md                    # This file
├── input/                       # Place your Claude export files here
│   ├── conversations.json
│   ├── projects.json
│   └── users.json
├── output/                      # Converted files will appear here
│   └── claude_history/          # Your conversion output
└── src/                         # Source code
    └── convert_enhanced.py      # The conversion engine
```

## What You Get

```
output/claude_history/
├── conversations/
│   └── 2024/
│       └── 03-March/
│           └── 15/
│               └── Your_Conversation_Title_abc123/
│                   ├── metadata.json
│                   └── messages/
│                       ├── 001_human_message.md
│                       ├── 002_assistant_message.md
│                       └── code_snippets/
│                           └── snippet_00.py
├── projects/
│   └── Your_Project_Name_xyz789/
│       ├── metadata.json
│       └── documents/
├── conversations_index.json
├── projects_index.json
└── users.json
```

## Requirements

- Python 3.6+
- Unix-like environment (Linux, macOS, WSL on Windows)

## Advanced Usage

### Using with Obsidian

The converted output is perfect for Obsidian:
1. Open Obsidian and create a new vault or use an existing one
2. Copy the contents of `output/claude_history/` to your vault
3. Enable the Graph View to see your knowledge network
4. Use the conversation tags to find all messages from a specific conversation

### Customizing the Conversion

You can modify `src/convert_enhanced.py` to:
- Change keyword extraction parameters
- Modify file naming conventions
- Add custom metadata fields
- Filter specific conversations

## License

MIT