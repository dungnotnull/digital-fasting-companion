<div align="center">

<img src="https://raw.githubusercontent.com/dungnotnull/digital-fasting-companion/main/browser-extension/icons/icon128.png" width="128" height="128" alt="Digital Fasting Companion">

# Digital Fasting Companion

### Reclaim Your Attention. Restore Deep Thinking.

*A privacy-first AI behavioral guardian that monitors digital habits, detects cognitive fatigue through multi-signal ML analysis, and enforces healthy offline breaks with real-world challenges.*

---

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white)](https://python.org)
[![License MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Privacy First](https://img.shields.io/badge/privacy-100%25%20local-important)](docs/privacy.md)
[![Chrome MV3](https://img.shields.io/badge/chrome-MV3-yellow?logo=googlechrome)](browser-extension/)

</div>

---

## The Problem

The average knowledge worker checks their phone **96 times per day**. AI chatbots and social media are engineered to maximize engagement, not cognitive wellbeing. We're outsourcing our thinking to machines, and our capacity for deep, independent work is eroding.

> *"The ability to perform deep work is becoming increasingly rare at exactly the same time it is becoming increasingly valuable."* — Cal Newport, *Deep Work*

**Information Overload** costs the US economy an estimated **$997 billion per year** in lost productivity. Your brain's working memory has strict capacity limits — and modern digital tools push it past the breaking point daily.

### The Science

| Concept | Key Insight |
|---------|------------|
| **Cognitive Load Theory** (Sweller, 1988) | Working memory capacity is limited to ~7±2 chunks. Information overload maximizes extraneous load, crowding out productive thinking. |
| **Attention Restoration Theory** (Kaplan, 1995) | Directed attention is a depletable resource. Restoration requires "fascination" (effortless attention) and "being away" from demands. |
| **Keystroke Dynamics** | Typing speed declines 15-25% under cognitive fatigue; error rates increase 30-40%. These signals are measurable passively with zero hardware. |
| **Heart Rate Variability** | HRV is a validated autonomic stress proxy across hundreds of studies. Low HRV = sympathetic dominance = stressed/fatigued state. |

---

## How It Works

```
    ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
    │   MONITOR    │ ──→ │   DETECT     │ ──→ │  INTERVENE   │
    │              │     │              │     │              │
    │ Screen time  │     │ 7-feature ML │     │ Tier 1: Nudge│
    │ Keystroke    │     │ fatigue score│     │ Tier 2: Soft │
    │ dynamics     │     │ [0.0 - 1.0]  │     │ Tier 3: Hard │
    │ HRV (opt)    │     │              │     │   + Overlay  │
    └──────────────┘     └──────────────┘     └──────┬───────┘
                                                     │
                      ┌──────────────────────────────┘
                      ▼
    ┌─────────────────────────────────────────────────────┐
    │               CHALLENGE GENERATION                  │
    │                                                     │
    │  Claude API ──→ GPT-4 ──→ TinyLlama ──→ Static Pool│
    │  (premium)      (alt)     (local)       (always on) │
    └──────────────────────────┬──────────────────────────┘
                               ▼
    ┌─────────────────────────────────────────────────────┐
    │                  RECOVERY                           │
    │                                                     │
    │  User completes offline challenge → Lock released  │
    │  Quality rated → Model adapts → Cycle repeats      │
    └─────────────────────────────────────────────────────┘
```

### The 3-Tier Graduated Intervention System

| Tier | Score Range | Action | User Experience |
|------|------------|--------|----------------|
| **Tier 1** | 0.4 – 0.6 | Nudge notification | Desktop toast: "You've been online for a while. Take a moment to breathe?" |
| **Tier 2** | 0.6 – 0.8 | Soft lock | All windows minimize. Guided 2-minute box-breathing animation begins. |
| **Tier 3** | 0.8 – 1.0 | Hard lock | **API domains blocked via OS firewall.** Full-screen overlay with a real-world challenge that must be completed to restore access. |

### The ML Fatigue Detection Pipeline

The system computes a **7-dimensional feature vector** every 60 seconds:

```
Feature Vector = [typing_wpm, error_rate, backspace_ratio,
                  session_duration_min, app_switch_rate,
                  hour_of_day, hrv_score]
```

**Phase 1:** Rule-based heuristics (cold start)  
**Phase 2:** Personalized `scikit-learn` RandomForest trained on your 7-day usage baseline  
**Phase 3:** Online learning — model retrains weekly on accumulated labeled data, adapts to your changing patterns

No two users are alike. A developer types differently than a writer. The model learns **your** baseline and detects deviations from **your** normal.

### Challenge Categories (20 Handcrafted + AI-Generated)

| Category | Examples | Restores |
|----------|----------|----------|
| 🏃 **Physical** | Walk outside, pushups, breathing, stair climb | Autonomic balance, cortisol reduction |
| 🎨 **Creative** | Haiku, doodle, origami, letter writing | Divergent thinking, flow state |
| 👥 **Social** | Call a friend, give a compliment, help someone | Oxytocin, social connection |
| 🧠 **Introspective** | Journaling, body scan, trigger identification, gratitude | Metacognition, self-regulation |

---

## Quick Start

```bash
# Clone
git clone https://github.com/dungnotnull/digital-fasting-companion.git
cd digital-fasting-companion

# Install core dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env — set DB_KEY to any string (used for encryption)

# Verify everything works
python -m src.main test

# Run the full simulated workflow
python -m src.main demo

# Start monitoring for real
python -m src.main run
```

### Optional: Premium Challenge Generation

```bash
# Get keys from console.anthropic.com or platform.openai.com
# Add to .env:
CLAUDE_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-proj-...

# Or install locally (free, offline):
# 1. Install Ollama from https://ollama.ai
# 2. ollama pull tinyllama
```

---

## Privacy & Security

**This is a privacy-first project. Full stop.**

| Principle | Implementation |
|-----------|---------------|
| 🔒 **100% Local** | All behavioral data stays on your device. Zero telemetry. Zero cloud sync. |
| 🔐 **AES-256-GCM Encryption** | SQLite database encrypted at rest. Data is unreadable without your key. |
| ⌨️ **No Raw Keystrokes** | Only aggregate metrics (WPM, error rate, backspace ratio). Never individual keys. |
| 🔑 **OS Keychain Storage** | API keys stored in Windows Credential Manager / macOS Keychain. Never plain text. |
| 🌐 **No External Calls by Default** | Network calls only happen when you explicitly configure external APIs. |
| 🗑️ **Right to Erasure** | `python -m src.main delete` — one command wipes everything. No traces. |
| 📤 **Data Portability** | `python -m src.main export` — all your data as JSON. Take it anywhere. |

[Full Privacy Policy →](docs/privacy.md)

---

## Architecture

```
src/
├── agent/              Challenge generation (pluggable LLM backends)
│   ├── router.py           Priority fallback chain: Claude → GPT → Ollama → Static
│   ├── claude_backend.py   Retry logic, rate limiting, prompt caching
│   ├── openai_backend.py   GPT-4o with response_format JSON
│   ├── ollama_backend.py   Local TinyLlama via REST API
│   ├── static_pool.py      20 handcrafted offline challenges
│   ├── user_context.py     Context-aware challenge personalization
│   └── quality_tracker.py  Rating analytics, fine-tune triggers
│
├── biometrics/         Wearable HRV & stress data integration
│   ├── garmin_backend.py   Garmin Connect (HRV, stress, sleep)
│   └── apple_health.py     HealthKit stub (iOS companion)
│
├── config/             Settings, encryption, key management
│   ├── settings.py          Pydantic-settings from .env
│   └── key_manager.py       OS keychain for API key storage
│
├── detector/           Fatigue detection engine
│   ├── ml_fatigue_detector.py  RandomForest + online learning
│   ├── feature_pipeline.py     7-feature extraction, normalization
│   ├── fatigue_model.py        Rule-based fallback (cold start)
│   └── baseline_collector.py   7-day data collection with persistence
│
├── intervention/       3-tier graduated intervention system
│   ├── lock_engine.py        OS firewall rules, app minimize, notifications
│   ├── breathing_timer.py    Guided box-breathing (Tier 2)
│   └── challenge_pool.json  20 curated offline challenges
│
├── knowledge/          Self-improving research crawler
│   ├── crawler.py            ArXiv + Semantic Scholar fetcher
│   └── relevance_scorer.py   Domain-specific paper scoring
│
├── monitor/            Behavioral data collection
│   ├── screen_time.py        Cross-platform active app tracking
│   └── keystroke.py          Typing dynamics (WPM, errors, backspaces)
│
├── storage/            Encrypted persistence
│   └── local_db.py           AES-256-GCM SQLite with full CRUD
│
├── ui/                 Desktop interfaces
│   ├── overlay.html          Full-screen challenge overlay
│   ├── dashboard.html        Real-time usage dashboard
│   ├── settings.html         Full configuration panel
│   └── system_tray.py        Taskbar icon with status colors
│
├── scheduler.py        Weekly knowledge crawler + model retraining
└── main.py             CLI entry point (run, demo, test, export, delete)
```

**Python 3.11+** backend. **HTML/CSS/JS** frontend. **Chrome MV3** browser extension.  
No Electron bloat. No cloud dependency. No telemetry.

---

## CLI Commands

| Command | What It Does |
|---------|-------------|
| `python -m src.main run` | Start the background monitoring daemon |
| `python -m src.main demo` | Run a complete simulated E2E workflow |
| `python -m src.main test` | Verify all 12 components initialize correctly |
| `python -m src.main db-init` | Initialize/re-initialize the encrypted database |
| `python -m src.main export` | Export all your data as JSON |
| `python -m src.main delete` | Permanently delete all local data |

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Runtime** | Python 3.11+ |
| **Desktop UI** | HTML/CSS/JS (served locally) |
| **Browser Extension** | Chrome Manifest V3 (JavaScript) |
| **ML Engine** | scikit-learn RandomForest + online learning |
| **Local LLM** | Ollama + TinyLlama-1.1B (optional) |
| **Premium LLM** | Claude API (Sonnet-4) / OpenAI GPT-4o (optional) |
| **Database** | SQLite + AES-256-GCM encryption |
| **Process Monitoring** | psutil + Win32 API / macOS AppKit |
| **Keystroke Capture** | pynput (aggregate metrics only) |
| **Task Scheduling** | APScheduler (with simple timer fallback) |
| **API Key Storage** | OS keychain (keyring) |
| **Packaging** | PyInstaller |
| **Wearable Integration** | Garmin Connect (HRV, stress, sleep) |

---

## Browser Extension

A Chrome MV3 extension in `browser-extension/`:

- **Detects** when you visit ChatGPT, Claude, Twitter, YouTube, Reddit, TikTok, Instagram, and 15+ other tracked sites
- **Tracks** session time per domain category
- **Reports** to the desktop daemon via Chrome Native Messaging
- **Shows** a hard lock overlay when Tier 3 intervention triggers

Load as unpacked extension from `browser-extension/` in `chrome://extensions`.

---

## Roadmap

| Phase | Status | Description |
|-------|--------|-------------|
| ✅ Phase 0 | Complete | Research, schema design, ADR, dev environment |
| ✅ Phase 1 | Complete | MVP — monitoring, rule-based intervention, static challenges |
| ✅ Phase 2 | Complete | ML integration — RandomForest, feature pipeline, local SLM |
| ✅ Phase 3 | Complete | Premium APIs — Claude, GPT-4o, browser extension, settings UI |
| ✅ Phase 4 | Complete | Knowledge loop — auto-crawler, paper scoring, scheduler |
| ✅ Phase 5 | Complete | Documentation, packaging, privacy policy |

### What's Next

- 📱 **Mobile companion app** (iOS/Android via React Native)
- 🧠 **Fine-tuned challenge model** based on collected quality ratings
- 📊 **Organization dashboard** for HR/wellness teams
- 🔬 **Real keystroke dynamics dataset** integration (KDD, UIST papers)
- 🎯 **Circadian rhythm awareness** — dynamic thresholds based on chronotype

---

## Contributing

This is an open-source project with a clear mission: help people reclaim their attention in the age of AI. Contributions are welcome.

See [CONTRIBUTING.md](docs/contributing.md) for development setup and guidelines.

**Core principles for contributions:**
- Privacy-first — no telemetry, no cloud sync, no data exfiltration
- Local-first — everything works offline by default
- User-controlled — all interventions configurable, all data exportable/deletable
- Test before submit — `python -m src.main test` must pass

---

## Research Foundation

This project is grounded in established cognitive science and behavioral psychology:

- **Miller (1956):** The magical number 7±2 — working memory capacity limits
- **Sweller (1988):** Cognitive Load Theory — intrinsic, extraneous, and germane load
- **Kaplan & Kaplan (1989, 1995):** Attention Restoration Theory — fascination and being away
- **Newport (2016):** Deep Work — the competitive advantage of focused cognition
- **Kahneman (1973):** Attention and Effort — limited attentional capacity model
- **Stothart et al. (2015):** Even unread phone notifications reduce attention
- **Sievertsen et al. (2016):** Cognitive fatigue measurably degrades standardized test performance

Full research bibliography in [SECOND-KNOWLEDGE-BRAIN.md](SECOND-KNOWLEDGE-BRAIN.md).

---

<div align="center">

### "The ability to perform deep, focused cognitive work is the new competitive advantage."

*Digital Fasting Companion helps you protect it.*

---

**[Installation Guide](docs/installation.md)** · **[Privacy Policy](docs/privacy.md)** · **[API Setup](docs/api-setup.md)** · **[Contributing](docs/contributing.md)**

Made with ❤️ for anyone who wants their attention back.

</div>
