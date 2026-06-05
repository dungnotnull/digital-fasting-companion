# SECOND-KNOWLEDGE-BRAIN.md — digital-fasting-companion
**Domain:** Digital Wellbeing | Cognitive Fatigue Detection | Behavioral Intervention Design  
**Knowledge Version:** 1.0  
**Last Updated:** 2026-06-03  
**Maintainer:** Auto-crawler (weekly) + manual additions

---

## 1. Core Concepts & Theoretical Foundations

### 1.1 Information Overload
Information Overload occurs when the volume, velocity, or variety of incoming information exceeds an individual's cognitive processing capacity. First formalized by Alvin Toffler (Future Shock, 1970). Key measurable consequences: decision paralysis, reduced recall accuracy, increased error rates, and elevated cortisol.

### 1.2 Cognitive Load Theory (CLT)
Developed by John Sweller (1988). Working memory has a strict capacity limit (~7±2 chunks, Miller 1956). CLT distinguishes three load types:
- **Intrinsic load:** Task complexity (fixed for given task)
- **Extraneous load:** Poor information design (reducible)
- **Germane load:** Schema formation / learning (productive)
Information overload maximizes extraneous load, crowding out germane load.

### 1.3 Attention Restoration Theory (ART)
Kaplan & Kaplan (1989, 1995). Directed attention is a depletable resource. Restoration requires "fascination" (effortless attention, e.g., nature) and "being away" from demands. Key implication: meaningful offline breaks must have ART properties to actually restore cognitive capacity — scrolling social media is not restorative.

### 1.4 Deep Work Framework
Cal Newport (2016). Deep Work = professional activities performed in a state of distraction-free concentration that push cognitive capabilities to their limit. Shallow Work = noncognitive, logistical tasks. Newport argues that the ability to do Deep Work is becoming rare and valuable in the AI age.

### 1.5 Behavioral Addiction Model (Digital)
Davis (2001) adapted substance addiction models to problematic internet use (PIU). Key construct: maladaptive cognitions about the self and the world, reinforced by variable-ratio reward schedules (social media likes, AI response quality). Intervention design should address both behavioral patterns and underlying cognitions.

### 1.6 Keystroke Dynamics as Cognitive State Proxy
Typing behavior (WPM, error rate, inter-key timing) changes measurably under cognitive fatigue and stress. Studies show: WPM decreases ~15–25% under high cognitive load; error rate increases ~30–40%; inter-key variability (entropy) increases. These signals are collectible passively without any additional hardware.

### 1.7 Heart Rate Variability (HRV) as Stress Proxy
HRV = variation in time between consecutive heartbeats. High HRV = parasympathetic dominance = relaxed/recovered state. Low HRV = sympathetic dominance = stressed/fatigued. HRV has been validated across hundreds of studies as a reliable, non-invasive proxy for autonomic nervous system state and cognitive readiness.

---

## 2. Key Research Papers

| Title | Authors | Year | Venue | DOI / Link | Relevance |
|-------|---------|------|-------|-----------|-----------|
| The Attentional Cost of Receiving a Cell Phone Notification | Stothart, Mitchum, Yehnert | 2015 | J. Experimental Psychology | 10.1037/xge0000100 | Notification design; even unread notifications reduce attention |
| No A, B, C for Cell Phone Use: Measuring Mobile Phone Use and Self-Regulation | Bayer et al. | 2016 | Communication Research | 10.1177/0093650214548048 | Self-regulation failure patterns for smartphone use |
| Measuring the Effects of Information Overload on Employee Performance | Butt, Ahmad | 2020 | Behaviour & IT | 10.1080/0144929X.2020.1807048 | Quantified productivity loss from overload |
| Cognitive Load While Using Smartphones | Cecchinato et al. | 2019 | CHI | 10.1145/3290605.3300455 | CHI study on smartphone-induced cognitive load |
| Digital Detox: An Effective Solution to Social Media Addiction? | Schmuck | 2020 | Cyberpsychology, Behavior | 10.1089/cyber.2019.0255 | Effectiveness evidence for digital fasting interventions |
| Keystroke Dynamics Authentication | Ayotte, Wu, Bhanu | 2020 | IEEE TIFS | 10.1109/TIFS.2020.3008916 | Keystroke features for behavioral biometrics (transferable to fatigue detection) |
| Cognitive Fatigue Influences Students' Performance on Standardized Tests | Sievertsen, Gino, Piovesan | 2016 | PNAS | 10.1073/pnas.1516947113 | Cognitive fatigue measurably degrades performance |
| Heart Rate Variability: Measurement and Clinical Utility | Kleiger, Stein, Bigger | 2005 | Annals of Noninvasive Electrocardiology | 10.1111/j.1542-474X.2005.10103.x | HRV as validated biomarker for autonomic state |
| Attention and Effort | Kahneman, D. | 1973 | Prentice-Hall | (Book) | Foundational: limited attentional capacity model |
| Screen Time and Children | Twenge, Campbell | 2018 | Preventive Medicine Reports | 10.1016/j.pmedr.2018.10.003 | Correlational evidence: screen time and wellbeing |
| Tech Addiction — When Problematic Use of Digital Technology Becomes a Mental Disorder | Brand et al. | 2019 | Current Addiction Reports | 10.1007/s40429-019-00248-y | Clinical framing of tech dependency |
| Technoference: Parent Distraction with Technology and Associations with Child Behavior | McDaniel, Radesky | 2018 | Child Development | 10.1111/cdev.12822 | Cross-generational digital fatigue effects |
| An Empirical Study on Detecting Cognitive Load Using Physiological Signals | Nourbakhsh et al. | 2017 | PLOS ONE | 10.1371/journal.pone.0169166 | Multi-signal (GSR + HRV + EEG) cognitive load detection |
| Reclaiming the Conversation: The Power of Talk in a Digital Age | Turkle, S. | 2015 | Penguin Press | (Book) | Qualitative evidence for deep human connection recovery |

---

## 3. State-of-the-Art ML/DL Models

### 3.1 Emotion & Stress Detection (HuggingFace)
| Model ID | Task | Params | Inference | Notes |
|----------|------|--------|-----------|-------|
| j-hartmann/emotion-english-distilroberta-base | Emotion classification (7 labels) | 67M | CPU ~300ms | Best precision for stress/surprise detection |
| cardiffnlp/twitter-roberta-base-emotion | Emotion classification (4 labels) | 125M | CPU ~500ms | Robust on informal text |
| SamLowe/roberta-base-go_emotions | Fine-grained emotion (28 labels) | 125M | CPU ~500ms | Most granular; good for journaling-style prompts |

### 3.2 Local SLM for Challenge Generation (HuggingFace via Ollama)
| Model ID | Params | Quantization | VRAM/RAM | Quality |
|----------|--------|-------------|----------|---------|
| TinyLlama/TinyLlama-1.1B-Chat-v1.0 | 1.1B | GGUF Q4 | ~700MB RAM | Good for simple instruction-following |
| microsoft/phi-2 | 2.7B | GGUF Q4 | ~1.7GB RAM | Better reasoning, recommended if RAM allows |
| Qwen/Qwen2.5-3B-Instruct | 3B | GGUF Q4 | ~2GB RAM | Strong multilingual support |

### 3.3 Behavioral Fatigue Classification (Custom Local Model)
No pretrained model exists for this exact task. Recommended approach:
- **Algorithm:** scikit-learn `RandomForestClassifier` (n_estimators=100, max_depth=8)
- **Features:** 7-dimensional vector (typing_wpm, error_rate, backspace_ratio, session_min, app_switch_rate, hour_of_day, hrv_score)
- **Training:** User's own 7-day labeled data (self-reported fatigue events)
- **Alternative:** `GradientBoostingClassifier` — typically 3–5% better precision but 10x slower training
- **Baseline benchmark:** Static threshold rules (80% precision, 45% recall) vs. ML model (target: 78% precision, 65% recall)

---

## 4. Tools, Libraries & Frameworks

| Tool | Purpose | GitHub / Source |
|------|---------|----------------|
| crawl4ai | Fast async web crawler for knowledge base updates | github.com/unclecode/crawl4ai |
| Ollama | Local LLM runtime (GGUF models) | ollama.ai / github.com/ollama/ollama |
| pynput | Cross-platform keystroke monitoring | pypi.org/project/pynput |
| psutil | Cross-platform process + system monitoring | github.com/giampaolo/psutil |
| SQLCipher | AES-256 encrypted SQLite | github.com/sqlcipher/sqlcipher |
| Tauri | Lightweight cross-platform desktop apps (Rust + WebView) | tauri.app |
| APScheduler | In-process task scheduling | github.com/agronholm/apscheduler |
| keyring | OS keychain integration (API key storage) | github.com/jaraco/keyring |
| arxiv (Python) | ArXiv paper search and metadata | pypi.org/project/arxiv |
| scikit-learn | ML model training and inference | scikit-learn.org |
| anthropic | Official Claude API SDK | pypi.org/project/anthropic |

---

## 5. Self-Update Protocol

### 5.1 Overview
The SECOND-KNOWLEDGE-BRAIN.md is automatically updated weekly by a crawler agent (`src/knowledge/crawler.py`). New papers and models found are appended to Section 2 and Section 3 respectively, and logged in Section 7.

### 5.2 Crawler Configuration (crawl4ai)

**Source 1: ArXiv**
```python
ARXIV_QUERIES = [
    "ti:(cognitive fatigue) AND cat:(cs.HC)",
    "ti:(digital wellbeing) AND cat:(cs.HC OR cs.AI)",
    "ti:(attention span) AND cat:(cs.HC)",
    "ti:(information overload) AND cat:(cs.HC OR cs.IR)",
    "ti:(screen time intervention) AND cat:(cs.HC)",
    "ti:(keystroke dynamics fatigue) AND cat:(cs.CV OR cs.HC)",
    "abs:(HRV cognitive load wearable) AND cat:(cs.HC)",
    "ti:(behavioral addiction digital) AND cat:(cs.HC)",
]
ARXIV_MAX_RESULTS_PER_QUERY = 5
ARXIV_SORT_BY = "submittedDate"  # newest first
```

**Source 2: HuggingFace Papers**
```
URL: https://huggingface.co/papers?q={query}
Queries: "emotion recognition", "cognitive load", "mental fatigue detection", "wellbeing monitoring"
```

**Source 3: Papers with Code**
```
URL: https://paperswithcode.com/search?q_meta={query}&q_type=paper
Queries: "fatigue detection", "attention span", "emotion recognition real-time", "behavioral biometrics"
```

**Source 4: Semantic Scholar**
```
API: https://api.semanticscholar.org/graph/v1/paper/search
Queries: "digital wellbeing intervention", "screen time mental health", "cognitive fatigue keyboard"
Fields: title, authors, year, citationCount, externalIds, tldr
Filter: citationCount >= 5, year >= 2020
```

### 5.3 Update Frequency
- **Automated:** Every Sunday at 02:00 local time via APScheduler
- **Manual trigger:** `python -m src.knowledge.crawler --force`
- **Rate limit:** Max 50 papers evaluated per run; top 5 by relevance score added to knowledge base

### 5.4 Relevance Scoring
Papers are scored using cosine similarity between paper abstract embedding and domain centroid embedding:
```python
DOMAIN_KEYWORDS = [
    "cognitive fatigue", "information overload", "attention span",
    "digital wellbeing", "screen time", "HRV", "keystroke dynamics",
    "behavioral intervention", "mental health smartphone", "deep work"
]
RELEVANCE_THRESHOLD = 0.65  # minimum cosine similarity to be included
```
Embedding model: `sentence-transformers/all-MiniLM-L6-v2` (local, 22MB)

### 5.5 New Entry Format
When adding a new paper to Section 2, use this table row format:
```
| {Title} | {Authors (first 3 only)} | {Year} | {Venue} | {DOI or arXiv:XXXX.XXXXX} | {1-sentence relevance note} |
```
When adding a new HuggingFace model to Section 3, use the existing table format with model ID, task, params, and notes.

### 5.6 Conflict / Duplication Rules
- Deduplicate by DOI (exact match) or arXiv ID
- If same paper appears under different titles, keep the more cited version
- Update existing row rather than adding duplicate if DOI matches

---

## 6. Domain Ontology (For Crawler Relevance Scoring)

```
digital-fasting-companion domain:
├── Behavioral Psychology
│   ├── Cognitive Load Theory
│   ├── Attention Restoration Theory
│   ├── Behavioral Addiction
│   └── Self-Regulation / Willpower
├── Physiological Signals
│   ├── Heart Rate Variability (HRV)
│   ├── Galvanic Skin Response (GSR)
│   └── Keystroke Dynamics
├── Digital Behavior
│   ├── Screen Time Measurement
│   ├── App Usage Patterns
│   └── Information Overload
├── ML/DL for Wellbeing
│   ├── Fatigue Detection Models
│   ├── Emotion Recognition
│   └── Behavioral Biometrics
└── Intervention Design
    ├── Digital Nudges
    ├── Graduated Lockdown
    └── Real-World Challenge Design
```

---

## 7. Knowledge Update Log

| Date | Source | Papers Added | Models Added | Notes |
|------|--------|-------------|-------------|-------|
| 2026-06-03 | Manual seed | 14 papers | 7 models | Initial knowledge base population |

---

*This file is auto-updated weekly by `src/knowledge/crawler.py`. Manual additions are welcome — follow Section 5.5 format.*
