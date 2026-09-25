# kaka.ai — AI Agent with 66 Local Tools

A local AI agent with access to file ops, web browsing, code analysis, and more. Runs from any terminal via `kaka`.

## Quick Start

```bash
# From any directory
kaka "What time is it?"
kaka "List files in /tmp"
kaka "Read file /etc/hostname"

# Interactive mode
kaka
```

## Installation

### Prerequisites
- Python 3.10+
- An API key from [OpenRouter](https://openrouter.ai/keys) (free tier available)

### Setup

```bash
# Clone or navigate to kaka.ai
cd /path/to/kaka.ai

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY
```

### Make `kaka` Available Globally

```bash
# Create the launcher shim
cat > ~/.local/bin/kaka << 'EOF'
#!/bin/bash
exec "/path/to/kaka.ai/venv/bin/python" "/path/to/kaka.ai/cli.py" "$@"
EOF

chmod +x ~/.local/bin/kaka

# Ensure ~/.local/bin is on your PATH
export PATH="$HOME/.local/bin:$PATH"
```

## Usage

### Single-Shot Mode

```bash
kaka "your message here"
kaka --model google/gemma-4-31b-it:free "your message"
kaka --verbose "your message"
kaka --tools          # List all 66 tools
kaka --help           # Show CLI options
```

### Interactive Mode

```bash
kaka
```

Starts a rich terminal UI with:

```
┌──────────────────────────────────────────────────────────────┐
│   ___          _               __     __  ___   _ __  ___   │
│  / _ \  _   _ | |  __ _  ___  \ \   / / / _ \ | '_ \/ __| │
│ | | | || | | || | / _` |/ __|  \ \ / / | |_| || |_) \__ \ │
│ | |_| || |_| || || (_| | (__    \ V /  |  _  || .__/|___/ │
│  \__\_\ \__,_||_| \__,_|\___|    \_/   |_|  |_||_|   ___/ │
│                                                     |____| │
│  Model: nvidia/nemotron-3-super-120b-a12b:free • 66 tools  │
└──────────────────────────────────────────────────────────────┘
```

### Slash Commands

| Command    | Description                        |
|------------|------------------------------------|
| `/help`    | Show help and tips                 |
| `/tools`   | List all 66 tools by category      |
| `/model`   | View/switch LLM model              |
| `/history` | View conversation history          |
| `/theme`   | Cycle dark/light/neon themes       |
| `/mode`    | Show current online/offline mode   |
| `/offline` | Switch to offline mode (Ollama)    |
| `/online`  | Switch to online mode              |
| `/compact` | Toggle compact output              |
| `/reset`   | Clear conversation history         |
| `/quit`    | Exit kaka                          |

### Model Selection

```bash
# List available free models
/model

# Switch by number
/model 2

# Switch by name
/model google/gemma-4-31b-it:free
```

**Available free models:**
1. `nvidia/nemotron-3-super-120b-a12b:free` (default)
2. `google/gemma-4-31b-it:free`
3. `nvidia/nemotron-3.5-lightning:free`
4. `inclusionai/ling-3.0-flash-fin:free`
5. `cohere/north-mini-code:free`
6. `z-ai/glm-5.2:free`
7. `minimax/minimax-m3:free`

## Tools (66 total)

### 📁 File Operations (8)
`read_file`, `write_file`, `edit_file`, `list_directory`, `file_info`, `create_directory`, `move_file`, `copy_file`

### 🖥️ System (5)
`run_command`, `run_python`, `get_system_info`, `get_running_processes`, `kill_process`

### ⏰ DateTime (2)
`get_datetime`, `convert_timezone`

### 🌐 Web (4)
`web_search`, `fetch_url`, `browse_page`, `download_file`

### 💻 Code (6)
`analyze_code`, `format_code`, `find_in_codebase`, `code_stats`, `code_review`, `refactor_suggestion`

### 🧮 Math (3)
`calculate`, `unit_convert`, `random_number`

### 📊 Data (5)
`csv_inspect`, `json_transform`, `xml_parse`, `sql_query`, `data_summary`

### 📝 Content (5)
`write_file`, `create_template`, `summarize_text`, `text_transform`, `diff_texts`

### 🎨 Creative (3)
`generate_palette`, `color_info`, `lorem_ipsum`

### 🔧 Utility (6)
`uuid_generate`, `hash_text`, `base64_encode`, `timestamp_convert`, `text_stats`, `slugify`

### 🔒 Security (4)
`security_audit`, `check_dependencies`, `generate_password`, `check_secrets`

### 🌐 API (3)
`api_request`, `test_endpoint`, `graphql_query`

### 📈 DevOps (6)
`check_port`, `dns_lookup`, `traceroute`, `ssl_check`, `http_headers`, `ping_host`

### 🧠 Reasoning (2)
`reasoning`, `fact_check`

## Configuration

Environment variables in `.env`:

```bash
# Required
OPENROUTER_API_KEY=sk-or-v1-...

# Optional
MODEL_NAME=nvidia/nemotron-3-super-120b-a12b:free
PROVIDER=openrouter
MEMORY_DIR=/path/to/kaka.ai/memory
LOG_LEVEL=INFO
PRIVACY_MODE=false
ENCRYPT_DATA=false

# Fallback models (comma-separated)
FALLBACK_MODELS=nvidia/nemotron-3.5-lightning:free,google/gemma-4-31b-it:free
```

## Architecture

```
kaka.ai/
├── cli.py              # Entry point — argparse, single-shot + interactive dispatch
├── .env                # Configuration (API keys, model, provider)
├── core/
│   ├── config.py       # Config loading, provider detection
│   ├── engine.py       # LLM calls (OpenRouter/Gemini), tool-call parsing, multi-round loop
│   ├── agent.py        # Interactive UI with Rich, slash commands, prompt_toolkit
│   ├── tools.py        # ToolRegistry — schema registration, validation, execution
│   ├── builtins.py     # 66 built-in tools across 12 categories
│   ├── ui.py           # Rich UI components (panels, tables, banners, themes)
│   └── telemetry.py    # Usage tracking
├── server.py           # Optional FastAPI HTTP API
├── requirements.txt    # Python dependencies
└── memory/             # Persistent memory storage
```

## Rate Limits

The free tier on OpenRouter has daily request limits. If you hit 429 errors:
1. Wait for the limit to reset (next day)
2. Add credits at https://openrouter.ai/settings/credits ($5 unlocks 1000 free requests/day)
3. Switch to a different free model with `/model`

## License

MIT
