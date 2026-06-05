# Installation Guide

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Windows 10 / macOS 13 | Windows 11 / macOS 14+ |
| Python | 3.11+ | 3.12 |
| RAM | 4GB | 8GB+ (for local LLM) |
| Disk | 200MB | 2GB+ (with Ollama models) |
| GPU | None required | Optional for Ollama |

## Windows Installation

```powershell
# 1. Install Python 3.11+ from python.org
#    Check "Add Python to PATH" during installation

# 2. Open Command Prompt or PowerShell
cd C:\path\to\digital-fasting-companion

# 3. Create virtual environment (optional but recommended)
python -m venv .venv
.venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Copy and configure environment
copy .env.example .env
# Edit .env with a text editor — set DB_KEY

# 6. Run the test
python -m src.main test

# Expected output: "[OK] All tests passed"
```

## macOS Installation

```bash
# 1. Install Python 3.11+ via Homebrew
brew install python@3.12

# 2. Navigate to project
cd /path/to/digital-fasting-companion

# 3. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Configure
cp .env.example .env
# Edit .env — set DB_KEY

# 6. Run the test
python -m src.main test
```

## Optional: Install Ollama (for local challenge generation)

```bash
# Download and install from https://ollama.ai
# Then pull the model:
ollama pull tinyllama

# Verify it's running:
curl http://localhost:11434/api/tags
```

## Optional: Configure Premium LLM APIs

1. Get API keys from [console.anthropic.com](https://console.anthropic.com) or [platform.openai.com](https://platform.openai.com)
2. Add to `.env`:
   ```
   CLAUDE_API_KEY=sk-ant-...
   OPENAI_API_KEY=sk-...
   ```
3. Restart the daemon

Keys are automatically moved to the OS keychain on next run for secure storage.

## Troubleshooting

**pynput permission warning on macOS:**
System Preferences → Privacy & Security → Input Monitoring → add Terminal/Python

**Windows firewall rules require admin:**
`python -m src.main run` may need to be run as Administrator for domain blocking

**Ollama not connecting:**
Verify `OLLAMA_HOST=http://localhost:11434` and that `ollama serve` is running

**Database errors:**
Run `python -m src.main db-init` to re-initialize the schema
