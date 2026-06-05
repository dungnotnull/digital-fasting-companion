# API Key Setup Guide

This guide covers configuring premium LLM APIs for enhanced challenge generation.

## Overview

The Digital Fasting Companion uses a pluggable backend system for challenge generation:

| Priority | Backend | Required | Quality |
|----------|---------|----------|---------|
| 1 | Claude API (claude-sonnet-4-6) | API Key | Highest |
| 2 | OpenAI GPT-4o | API Key | High |
| 3 | Ollama + TinyLlama | Local install | Good |
| 4 | Static challenge pool | None | Baseline |

No API keys are required — the static pool provides 20 curated challenges across 4 categories as a permanent fallback.

## Claude API Setup

### 1. Get an API Key
- Visit https://console.anthropic.com
- Create an account or sign in
- Go to API Keys → Create Key
- Copy the key (starts with `sk-ant-api03-...`)

### 2. Add to Configuration

**Option A: Environment variable**
```bash
# In .env file:
CLAUDE_API_KEY=sk-ant-api03-your-key-here
```

**Option B: OS Keychain (recommended)**
```bash
# The app will prompt on first run, or you can set via:
python -c "from src.config.key_manager import get_key_manager; get_key_manager().set_key('claude', 'sk-ant-api03-...')"
```

### 3. Settings in .env

```bash
# Claude API daily call limit (default: 10)
CLAUDE_MAX_CALLS_PER_DAY=10

# Model selection
CLAUDE_MODEL=claude-sonnet-4-20250514
```

### 4. Verify
```bash
python -m src.main test
# Look for: "Agent: ChallengeGenerator ready (available: ['ClaudeBackend', ...])"
```

## OpenAI API Setup

### 1. Get an API Key
- Visit https://platform.openai.com/api-keys
- Create an account or sign in
- Create a new secret key
- Copy the key (starts with `sk-proj-...`)

### 2. Add to Configuration

**Option A: Environment variable**
```bash
OPENAI_API_KEY=sk-proj-your-key-here
```

**Option B: OS Keychain**
```bash
python -c "from src.config.key_manager import get_key_manager; get_key_manager().set_key('openai', 'sk-proj-...')"
```

### 3. Settings in .env

```bash
OPENAI_MAX_CALLS_PER_DAY=10
OPENAI_MODEL=gpt-4o
```

## Ollama Setup (Local SLM)

### 1. Install Ollama
- Download from https://ollama.ai
- Install the application
- Start the Ollama service

### 2. Pull Models
```bash
# Primary model (1.1B params, ~700MB RAM)
ollama pull tinyllama

# Alternative (2.7B, better reasoning, ~1.7GB RAM)
ollama pull phi

# Alternative (3B, multilingual)
ollama pull qwen2.5:3b
```

### 3. Configure

```bash
# In .env:
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=tinyllama
OLLAMA_TIMEOUT_SECONDS=30
```

### 4. Verify Ollama is running
```bash
curl http://localhost:11434/api/tags
# Should return model list with "tinyllama"
```

## Garmin Connect Setup

### 1. Create credentials
- Use your Garmin Connect account credentials
- Set in .env or keychain:

```bash
GARMIN_USERNAME=your-garmin-email@example.com
GARMIN_PASSWORD=your-garmin-password
```

### 2. Install the library
```bash
pip install garminconnect
```

### 3. What it provides
- HRV (heart rate variability) — objective stress/fatigue signal
- Resting heart rate
- Sleep score
- Stress score (0-100)

These biometric signals are integrated as the optional 8th feature in the fatigue detection model.

## Cost Estimates

| API | Model | Cost per Challenge | Daily Cap | Monthly Cost (10/day) |
|-----|-------|-------------------|-----------|----------------------|
| Claude | Sonnet-4 | ~$0.003 | 10 | ~$0.90 |
| OpenAI | GPT-4o | ~$0.002 | 10 | ~$0.60 |
| Ollama | TinyLlama | Free (local) | Unlimited | $0 |
| Static Pool | N/A | Free | Unlimited | $0 |

Costs are approximate based on ~200 output tokens per challenge at published API prices.

## Security Notes

- API keys are stored in your operating system's native keychain (Windows Credential Manager / macOS Keychain) — never in plaintext files
- The `.env` file is only used as a fallback; keys are migrated to keychain on first run
- API calls to Claude/OpenAI send only non-sensitive context metadata: time of day, fatigue score, activity category — no text content, keystroke data, or personal information is ever sent
