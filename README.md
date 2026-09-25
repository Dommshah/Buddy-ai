# Buddy.ai v2.1 — Vibrant Autonomous Assistant

Buddy.ai is a vibrant, multi-tool autonomous AI for your terminal — with the polished **kaka.ai design system**, rich CLI, streaming, and 49+ tools covering reasoning, learning, security, voice, and more.

![Buddy.ai Banner](https://img.shields.io/badge/Buddy.ai-v2.1-00D9FF?style=for-the-badge) ![Tools](https://img.shields.io/badge/tools-49-FFB74D?style=flat-square) ![Themes](https://img.shields.io/badge/themes-dark%20%7C%20light%20%7C%20neon-B967FF?style=flat-square)

## ✨ What's New in v2.1 (kaka.ai UI port)

- **RGB Animated Banner** `core/ui.py:120` — `BUDDY AI` ASCII art with cycling `#00D9FF` `#B967FF` `#00E676`
- **Categorized Tools Table** `core/ui.py:340` — 49 tools in 8 categories (Code, Cognition, Data, Memory, System, Voice, Web & Vision, Content)
- **Vibrant Panels** `cli.py:88` `core/agent.py:360` — `user_panel()` `agent_panel()` with Markdown, `tool_panel()`, `streaming` Live
- **Command Palette** `core/agent.py:95` `FuzzyWordCompleter` — Tab completion, `/help` `/tools` `/history` `/theme` `/mode` `/offline` `/online`
- **Status Bar & Toasts** `core/ui.py:175` `core/ui.py:280` — provider/model/tools/elapsed, streaming indicator
- **Offline Mode** `core/agent.py:12` `MODELS["4"]` — `qwen2.5:3b` via Ollama, `/offline` `/online` toggle, `--offline` flag

## Features

### Core
- **Tool Calling** `core/builtins.py:17` — 49 tools: `read_file`, `write_file`, `list_files`, `search_files`, `run_command`, `run_python`, `system_info`, `clipboard`
- **Persistent Memory** `core/memory.py:1` — notes, preferences, conversation history
- **Categorized UI** `core/ui.py:340` — grouped tools, help/history/stats panels
- **Multiple LLM** `core/config.py:1` — Gemini (online) + Ollama qwen2.5:3b (offline)

### Cognitive Abilities
- **Advanced Reasoning** `cognition/reasoning/engine.py:1` — chain-of-thought, tree-of-thought, deductive, inductive, abductive, analogical, critical, reflective (8 modes)
- **Adaptive Learning** `cognition/learning/adaptive.py:1` — patterns, recall, skill proficiency
- **Autonomous Planning** `cognition/autonomy.py:1` — decompose goals, prioritize, execute
- **Content Creation** `cognition/content.py:1` — blogs, emails, social, landing pages, video scripts
- **Code Analysis** `cognition/code_analysis.py:1` — complexity, bugs, generation
- **Security Auditing** `cognition/security.py:1` — vuln scan, secret detection
- **Pattern & Prediction** `cognition/patterns.py:1` — trends, linear regression, volatility
- **Verification** `cognition/verification.py:1` — fact-check, data integrity
- **Creativity** `cognition/creativity.py:1` — SCAMPER, brainstorming
- **Voice** `cognition/voice.py:1` `cognition/tts_engine.py:1` — STT/TTS, RVC
- **Data Analysis** `plugins/data.py:1` — json_stats, analyze_csv, convert_format

## Setup

```bash
# 1. Install (venv already at ./venv)
./venv/bin/python -m pip install -r requirements.txt

# 2. Configure API key
cp .env.example .env
# Edit .env and add GEMINI_API_KEY

# 3. Run Buddy
buddy                          # vibrant interactive (banner + status)
buddy --tools                  # categorized 49 tools
buddy --offline                # qwen2.5:3b offline
buddy "list my files"          # single-shot with streaming
./agent --help                 # launcher
```

## Usage

### Interactive (vibrant)
```bash
buddy
# Select model:
# 1 gemini-3.5-flash-lite (Recommended)
# 2 gemini-3.6-flash
# 3 gemini-3.1-pro-preview
# 4 qwen2.5:3b (Offline)
# → BUDDY banner + status bar + buddy> prompt
# /help    — commands
# /tools   — 49 categorized
# /history — last 20 turns
# /theme   — dark → light → neon
# /mode    — show ONLINE/OFFLINE
# /offline — switch to Ollama
# /online  — back to Gemini
# /compact — toggle compact
# /stats   — session time/messages/tools
# /clear   — clear screen
# /reset   — clear memory
# /voice   — voice mode
# quit     — exit
```

### Single Command (streaming)
```bash
buddy "analyze this Python code for bugs"
buddy "write a blog post about AI in healthcare"
buddy --offline "summarize README.md offline"
```

### As Library
```python
from core.agent import Agent
agent = Agent()  # loads .env
response = agent.chat("explain this code: def f(x): return x*2")
# streaming panel + tool_panel auto

agent.add_tool(
    name="greet",
    description="Say hello",
    func=lambda name: f"Hello, {name}!",
    parameters={"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}
)
```

## All 49 Tools — Categorized `core/ui.py:340`

| Category | Tools |
|----------|-------|
| **Code (3)** | `code_analyze`, `code_generate`, `security_audit` |
| **Cognition (3)** | `reason`, `autonomy_plan`, `autonomy_decide` |
| **Data (5)** | `calculate`, `json_query`, `pattern_detect`, `predict`, `verify` |
| **Memory (2)** | `save_memory`, `recall_memory`, `learn_store`, `learn_recall`, `knowledge_query`, `knowledge_store` |
| **Content (2)** | `content_create`, `creative_idea`, `creative_prompt` |
| **System (28)** | `read_file`, `write_file`, `list_files`, `search_files`, `run_command`, `run_python`, `system_info`, `clipboard`, `get_datetime`, `fetch_url`, `autonomous_reason`, `voice_*` (3), `agent_*` (3), `deep_research`, `browse_page`, `web_search`, `analyze_csv`, `json_stats`, `convert_format`, `platform_adapter`, `ponytail_*` (4) |
| **Voice (3)** | `voice_speak`, `voice_listen`, `voice_transcribe`, `voice_engines` |
| **Web & Vision (3)** | `browse_page`, `fetch_url`, `web_search` |

`buddy --tools` renders this as a rich table with `core/ui.py:340`.

## Configuration `.env.example:1`

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | — | **Required** Google Gemini key |
| `MODEL_NAME` | `gemini-2.0-flash` | Model override |
| `OFFLINE_MODEL` | `qwen2.5:3b` | Ollama model for `--offline`/`4` |
| `OLLAMA_BASE_URL` | `http://localhost:11434/v1` | Ollama endpoint |
| `MAX_TOKENS` | `4096` | Max response tokens |
| `TEMPERATURE` | `0.7` | 0-2 |
| `MEMORY_DIR` | `./data/memory` | Storage |
| `LOG_LEVEL` | `INFO` | Logging |

## Project Structure

```
Buddy.ai/  (ai-agent/)
├── buddy / agent             # Launchers → venv/bin/python cli.py
├── cli.py                    # Vibrant CLI — buddy, --tools, streaming `cli.py:88`
├── core/
│   ├── agent.py             # Buddy interactive `core/agent.py:145` banner+status+palette
│   ├── ui.py                # Design system `core/ui.py:1` themes/banner/panels (597 lines)
│   ├── engine.py            # LLM + tool loop `core/engine.py:1`
│   ├── config.py            # Config `core/config.py:1`
│   ├── tools.py             # Registry `core/tools.py:1`
│   ├── builtins.py          # 49 tools `core/builtins.py:17`
│   ├── memory.py
│   └── plugins.py
├── cognition/               # reasoning, learning, patterns, voice, security, content...
├── plugins/                 # web, data
├── data/                    # memory / learning
├── pyproject.toml           # name=buddy-ai v2.1.0 `pyproject.toml:2`
├── requirements.txt
└── venv/                    # venv with buddy/Buddy.ai binaries
```

## Verification

```bash
buddy --help
buddy --tools          # 49 categorized
./venv/bin/python live_test.py   # 44/44 PASS
./venv/bin/python simulation.py  # ALL SYSTEMS OPERATIONAL
printf "1\n/quit\n" | buddy  # banner + exit
```

## License

Private use only — Buddy.ai v2.1.
