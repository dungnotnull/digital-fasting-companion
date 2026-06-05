# PROJECT-detail.md — digital-fasting-companion

## Executive Summary
`digital-fasting-companion` is a privacy-first AI behavioral guardian that monitors user interaction with AI tools and social media, detects early-stage cognitive fatigue through multi-signal machine learning analysis, and enforces healthy digital breaks via a 3-tier graduated intervention system. When intervention is triggered, the agent locks relevant API access and presents real-world challenges that must be completed to restore access. The system operates entirely locally by default, with optional external LLM APIs for enhanced challenge generation.

---

## Problem Statement

### The Crisis
- The average knowledge worker checks their phone 96 times/day (Asurion, 2023)
- AI chatbot dependency is creating "cognitive outsourcing" — users lose the capacity for independent problem-solving
- Information Overload costs the US economy an estimated $997 billion/year in lost productivity (IDC, 2018)
- Social media and AI tools are engineered to maximize engagement, not cognitive wellbeing
- Gen Z attention spans have measurably decreased correlating with smartphone adoption (Twenge et al., 2018)

### Research-Backed Context
- **Cal Newport (Deep Work, 2016):** The ability to perform deep, focused cognitive work is the new competitive advantage; it is increasingly rare and increasingly valuable
- **Nicholas Carr (The Shallows, 2010):** Internet use is physically rewiring neural pathways, reducing capacity for linear, deep reading
- **Cognitive Load Theory (Sweller, 1988):** Working memory has strict capacity limits; information overload directly impairs learning, creativity, and decision quality
- **Attention Restoration Theory (Kaplan, 1995):** Directed attention is a finite resource requiring intentional recovery periods

---

## Target Users

### Primary Users
- Knowledge workers: software engineers, writers, researchers, product designers
- Students and academics experiencing attention fragmentation
- Professionals developing "AI dependency" anxiety

### Secondary Users
- Parents managing children's AI/screen time
- Digital wellbeing therapists and coaches recommending clinical tools
- HR teams implementing organizational wellness programs

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                      USER INTERFACE LAYER                        │
│    System Tray App (Electron/Tauri)   Browser Extension (MV3)    │
│    Mobile Companion (React Native)                               │
└────────────────────────┬─────────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────────┐
│                     MONITORING LAYER                             │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────────────┐ │
│  │ Screen Time  │  │   Keystroke    │  │  Wearable/HRV        │ │
│  │ Monitor      │  │   Dynamics     │  │  Integration         │ │
│  │ (OS API /    │  │   Analyzer     │  │  (Apple Health /     │ │
│  │  psutil)     │  │   (pynput)     │  │   Garmin — optional) │ │
│  └──────────────┘  └────────────────┘  └──────────────────────┘ │
└────────────────────────┬─────────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────────┐
│                 FATIGUE DETECTION ENGINE                         │
│  Scikit-learn RandomForestClassifier (local inference)           │
│  Input features:                                                 │
│    typing_wpm, error_rate, backspace_ratio, session_min,         │
│    app_switch_rate, hour_of_day, hrv_score (optional)            │
│  Output: fatigue_score ∈ [0.0, 1.0]                             │
│  Training: User's own 7-day baseline (adaptive online learning)  │
└────────────────────────┬─────────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────────┐
│              GRADUATED INTERVENTION ENGINE                       │
│  Tier 1 [0.4–0.6]: Notification nudge → 5-min mindfulness prompt│
│  Tier 2 [0.6–0.8]: Soft lock → guided 2-min breathing exercise  │
│  Tier 3 [0.8–1.0]: Hard lock → real-world challenge required     │
│                    → API gateway blocked (OS firewall rule)      │
└────────────────────────┬─────────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────────┐
│              CHALLENGE GENERATION ENGINE                         │
│  Fallback chain:                                                 │
│  1. Claude API (claude-sonnet-4-6)   [if CLAUDE_API_KEY set]     │
│  2. OpenAI GPT-4o                    [if OPENAI_API_KEY set]     │
│  3. Local SLM: TinyLlama-1.1B-Chat   [via Ollama]               │
│  4. Static challenge pool            [JSON, always available]    │
└────────────────────────┬─────────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────────┐
│                    DATA STORAGE LAYER                            │
│         SQLite (AES-256 via SQLCipher) — local only              │
│  Tables: usage_sessions, fatigue_events, challenges,             │
│          recovery_log, user_baseline, app_categories             │
└──────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

### Core Backend
| Component | Technology | Source |
|-----------|-----------|--------|
| Runtime | Python 3.11+ | python.org |
| Desktop App Shell | Tauri 2.0 (Rust + WebView) | tauri.app |
| Browser Extension | Chrome MV3 (TypeScript) | developer.chrome.com |
| Local Database | SQLite + SQLCipher (AES-256) | PyPI: sqlcipher3 |
| Task Scheduling | APScheduler 3.x | PyPI |
| Process Monitoring | psutil 5.9+ | PyPI |
| Keystroke Capture | pynput 1.7+ | PyPI |
| OS-level hooks (Win) | pywin32 | PyPI |
| OS-level hooks (Mac) | pyobjc-framework-Quartz | PyPI |
| HTTP client | httpx (async) | PyPI |
| Config management | pydantic-settings | PyPI |
| Encryption utilities | cryptography 42+ | PyPI |

### ML/AI Stack
| Component | Technology | Source |
|-----------|-----------|--------|
| Fatigue classifier | Scikit-learn RandomForestClassifier | PyPI |
| Feature engineering | pandas + numpy | PyPI |
| Model persistence | joblib | PyPI |
| Local SLM runtime | Ollama | ollama.ai |
| HuggingFace inference | transformers + torch | PyPI |

### External APIs (Optional)
| API | SDK | Purpose |
|-----|-----|---------|
| Claude API | anthropic>=0.25.0 | Personalized challenges |
| OpenAI | openai>=1.30.0 | Alternative challenges |
| Apple HealthKit | HealthKit (Swift/iOS) | HRV data |
| Garmin Connect | garminconnect (PyPI) | Biometric fatigue |

---

## ML/DL Models

### Fatigue Detection Model (Custom, Train Locally)
- **Algorithm:** RandomForestClassifier (scikit-learn)
- **Features (7):** `typing_wpm`, `error_rate`, `backspace_ratio`, `session_duration_min`, `app_switch_rate_per_hour`, `hour_of_day`, `hrv_score`
- **Training Data:** User's own first 7 days of usage (cold start) + labeled fatigue events
- **Why no pretrained model:** Fatigue signatures are highly individual; a user-specific baseline trained locally outperforms generic models on this task. No suitable public pretrained model exists for this exact multi-signal input.
- **Cold Start Strategy:** Use conservative static thresholds for Week 1, then switch to ML model after sufficient labeled data

### Emotion/Stress Signal Model (HuggingFace, Optional)
- **Model:** `j-hartmann/emotion-english-distilroberta-base`
- **Purpose:** Analyze tone of user's typed prompts as supplementary fatigue signal
- **Inference:** Local, CPU-compatible, ~300ms per inference
- **Note:** Supplement only — primary fatigue detection uses behavioral signals, not text content

### Local SLM for Challenge Generation (HuggingFace via Ollama)
- **Primary:** `TinyLlama/TinyLlama-1.1B-Chat-v1.0` — 1.1B params, runs on CPU
- **Alternative:** `microsoft/phi-2` — 2.7B params, better reasoning, requires modest GPU
- **Fine-tuning:** Not required initially; system prompt engineering sufficient for challenge generation
- **Fine-tune trigger:** If challenge quality score (user ratings) falls below 3.5/5 after 100 challenges

---

## External LLM API Integration Design

The challenge generation engine follows a **pluggable backend pattern** with a priority fallback chain:

```python
class ChallengeGenerator:
    backends = [
        ClaudeBackend(model="claude-sonnet-4-6"),   # highest quality
        OpenAIBackend(model="gpt-4o"),
        OllamaBackend(model="tinyllama"),            # local fallback
        StaticChallengePool(),                       # always available
    ]

    def get_challenge(self, user_context: UserContext) -> Challenge:
        for backend in self.backends:
            if backend.is_available():
                return backend.generate(user_context)
```

**Challenge prompt template (Claude/GPT):**
```
You are a digital wellbeing coach. The user has been using AI tools for {session_min} minutes 
and shows signs of cognitive fatigue. Generate ONE real-world challenge that:
1. Takes 10-15 minutes to complete offline
2. Requires no digital tools whatsoever
3. Is creative/physical/social (rotate category)
4. Is specific and actionable, not vague
User context: {time_of_day}, {fatigue_score}, {recent_activity_category}
```

---

## Feature Specification

### MVP Features (Phase 1 — 4 weeks)
- [ ] Cross-platform screen time monitoring (Windows + macOS)
- [ ] App usage categorization (AI tools / social media / productive / other)
- [ ] Time-threshold based Tier 3 intervention (>2h = hard lock)
- [ ] Static real-world challenge pool (20 challenges, offline)
- [ ] Basic local usage dashboard (daily/weekly)
- [ ] SQLite storage for usage sessions

### Advanced Features (Phase 2–3 — 8 weeks)
- [ ] Multi-signal ML fatigue detection (RandomForest, local training)
- [ ] Full 3-tier graduated intervention system
- [ ] Local SLM challenge generation (TinyLlama via Ollama)
- [ ] HRV integration (Apple Health / Garmin)
- [ ] Smart AI category whitelist (productive vs. entertainment)
- [ ] Circadian rhythm awareness (higher sensitivity in evenings)
- [ ] Recovery quality tracking (did the break actually help?)
- [ ] Weekly trend analytics with actionable insights

### Premium Features (Phase 4–5 — 4 weeks)
- [ ] Claude/GPT API integration for personalized deep challenges
- [ ] Optional social accountability (streak sharing with trusted contacts)
- [ ] Browser extension for web-based AI tools (ChatGPT, Claude.ai, etc.)
- [ ] Mobile companion app (iOS/Android)
- [ ] Organization-level dashboard for HR teams
- [ ] Export personal data report (PDF)

---

## E2E Data Flow

```
1.  System starts → load user's behavioral baseline from SQLite
2.  Every 30 seconds:
    a. Collect signals: (active_app, typing_wpm, error_rate, backspace_ratio)
    b. Append to rolling 5-minute feature window
3.  Every 60 seconds:
    a. Compute session_duration, app_switch_rate, hour_of_day
    b. fatigue_score = model.predict_proba(feature_vector)[1]
    c. Log to SQLite: usage_sessions table
4.  If fatigue_score crosses tier threshold:
    a. Determine tier (1, 2, or 3)
    b. Log to fatigue_events table
    c. For Tier 3:
       - Call challenge_generator.get_challenge(user_context)
         [Claude API → GPT-4 → TinyLlama → static pool]
       - Apply OS-level firewall rule to block AI API domains
       - Show full-screen overlay with challenge
5.  User completes challenge (timer-based or manual verification)
6.  On completion:
    a. Lift lock, restore API access
    b. Log to recovery_log (quality scored later by behavioral signals)
    c. Update online learning buffer for ML model
7.  Weekly: retrain RandomForest model on accumulated labeled data
8.  Weekly: SECOND-KNOWLEDGE-BRAIN crawl update (see crawler protocol)
```

---

## Privacy & Security

| Concern | Mitigation |
|---------|-----------|
| Behavioral data sensitivity | All data stored locally, SQLite + AES-256 encryption |
| API key exposure | Keys stored in OS keychain (keyring library), never in plain files |
| Keylogger perception | Only aggregate metrics collected (WPM, error rate) — no individual keystrokes stored |
| LLM API data leakage | Only non-sensitive contextual metadata sent (time_of_day, fatigue_score, activity_category) — no text content |
| Audit & trust | Full open-source codebase; user can export and delete all stored data in one click |

---

## Improvement Suggestions (Beyond Original Idea)

1. **Graduated 3-tier system** instead of binary lock — reduces user frustration and dropout
2. **Smart AI categorization** — productive AI use (coding, writing) has different limits than entertainment scrolling
3. **HRV wearable integration** — objective biometric data removes subjectivity; HRV is a validated proxy for cognitive load and autonomic stress
4. **Keystroke dynamics as fatigue signal** — typing speed decline + error rate increase is a well-researched cognitive fatigue indicator requiring no additional hardware
5. **Circadian rhythm awareness** — willpower is depleted in evenings; system is more sensitive 6PM–midnight
6. **Recovery quality scoring** — track whether the real-world challenge actually resulted in behavioral recovery (via post-break signal comparison)
7. **Adaptive personalization** — a developer types slower than a data entry clerk; user-specific ML baseline avoids false positives
8. **Challenge variety engine** — rotate challenge categories (physical, creative, social, introspective) and track which types produce the best recovery

---

## Key Dependencies (Python)

```
anthropic>=0.25.0       # Claude API (optional)
openai>=1.30.0          # GPT API (optional)
psutil>=5.9.8           # Process/system monitoring
scikit-learn>=1.4.2     # Fatigue ML classifier
transformers>=4.40.0    # HuggingFace SLM loading
torch>=2.2.0            # ML inference backend
sqlcipher3>=0.5.3       # AES-256 encrypted SQLite
apscheduler>=3.10.4     # Background task scheduling
pynput>=1.7.6           # Keystroke dynamics capture
httpx>=0.27.0           # Async HTTP client for APIs
keyring>=25.0.0         # Secure OS keychain for API keys
pydantic-settings>=2.2  # Config management
garminconnect>=0.2.0    # Garmin HRV data (optional)
cryptography>=42.0.0    # Encryption utilities
```
