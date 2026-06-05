# CLAUDE.md — digital-fasting-companion

## Project Identity
- **Name:** digital-fasting-companion
- **Folder:** D:\Dungchan\1
- **Tagline:** AI & Smartphone Addiction Recovery Companion
- **Status:** Phase 0 — Research & Setup

## Core Problem
Over-reliance on AI tools and social media is eroding human capacity for deep, independent thinking. Information Overload triggers measurable cognitive fatigue. This agent monitors digital behavior across AI chat apps and social media, detects early fatigue signals through multi-signal analysis, and enforces healthy offline breaks using a graduated 3-tier intervention system requiring real-world challenge completion to restore access.

## Architecture at a Glance
- **Platform:** Desktop-first (Windows + macOS) via system tray app + Browser Extension (Chrome/Firefox) + Mobile companion (iOS/Android)
- **Processing:** 100% local by default — all behavioral data stays on-device
- **Fatigue Detection:** Scikit-learn RandomForest trained on keystroke dynamics + session patterns (local)
- **Local SLM:** TinyLlama-1.1B-Chat via Ollama for real-world challenge generation
- **Optional LLM APIs:** Claude API (claude-sonnet-4-6) or GPT-4 for richer personalized challenges
- **Storage:** SQLite with AES-256 encryption (SQLCipher) — no cloud sync by default
- **OS Hooks:** Screen Time API (iOS), Digital Wellbeing API (Android), psutil + Win32/macOS APIs (desktop)

## Key Technical Decisions
1. **Privacy-first architecture**: Zero telemetry; all behavioral signals processed locally; API calls only when user explicitly opts in
2. **Graduated 3-tier intervention**: Tier 1 (score 0.4–0.6) = nudge notification; Tier 2 (0.6–0.8) = soft lock + breathing exercise; Tier 3 (0.8+) = hard API lock + real-world challenge
3. **Multi-signal fatigue detection**: typing speed + error rate + backspace frequency + session duration + time-of-day + optional HRV
4. **Smart categorization**: Distinguish productive AI use (coding assistant, writing) from passive/entertainment AI — different limits per category
5. **Adaptive baseline**: ML model personalizes to each user's individual typing and usage patterns via online learning; no hardcoded thresholds
6. **Pluggable LLM backend**: Fallback chain — Claude API → GPT-4 API → local TinyLlama → static challenge pool

## External LLM API Integrations (Optional, User-Configured)
| API | Use Case | Config Key |
|-----|----------|------------|
| Claude API (claude-sonnet-4-6) | Deep personalized real-world challenges | `CLAUDE_API_KEY` |
| OpenAI GPT-4o | Alternative high-quality challenge generation | `OPENAI_API_KEY` |
| Apple HealthKit | HRV data for objective stress/fatigue scoring | iOS only |
| Garmin Connect API | Advanced biometric fatigue data (HRV, stress) | `GARMIN_TOKEN` |

## HuggingFace Models in Use
| Model ID | Purpose | Notes |
|----------|---------|-------|
| TinyLlama/TinyLlama-1.1B-Chat-v1.0 | Local challenge generation | Run via Ollama |
| microsoft/phi-2 | Enhanced local reasoning (alternative SLM) | Run via Ollama |
| j-hartmann/emotion-english-distilroberta-base | Prompt tone / stress signal analysis | Inference locally |
| cardiffnlp/twitter-roberta-base-emotion | Secondary emotion classification | Inference locally |

## Current Active Development Tasks
- [ ] Phase 0: Set up Python 3.11+ environment + Electron/Tauri scaffold
- [ ] Phase 0: Research keystroke dynamics datasets (KDD, UIST papers)
- [ ] Phase 0: Evaluate Ollama local setup with TinyLlama on target hardware
- [ ] Phase 1: Implement OS-level screen time monitoring (psutil + Win32 API)
- [ ] Phase 1: Build SQLite schema + SQLCipher encryption layer
- [ ] Phase 1: Implement basic time-threshold intervention (MVP — no ML yet)
- [ ] Phase 1: Build challenge display overlay UI

## Reference Files
- `PROJECT-detail.md` — Full technical specification with architecture, tech stack, and features
- `PROJECT-DEVELOPMENT-PHASE-TRACKING.md` — Development roadmap with milestones and success criteria
- `SECOND-KNOWLEDGE-BRAIN.md` — Research papers, domain knowledge, and self-update protocol
