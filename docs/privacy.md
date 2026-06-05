# Privacy Policy

**Last Updated:** 2026-06-05

## Summary

The Digital Fasting Companion is designed with a **privacy-first, local-only architecture**. No usage data, behavioral signals, keystroke patterns, or personal information leaves your device unless you explicitly opt in to external API usage.

## Data We Store (Locally Only)

| Data | Storage Location | Encrypted |
|------|-----------------|-----------|
| App usage session times | Local SQLite (data/app.db) | Yes (AES-256-GCM) |
| App category classifications | Local SQLite | Yes |
| Fatigue event timestamps and scores | Local SQLite | Yes |
| Challenge titles and descriptions | Local SQLite | Yes (titles/descriptions) |
| Recovery log entries | Local SQLite | No (timestamps only) |
| Keystroke aggregate metrics (WPM, error rate, backspace ratio) | Local SQLite | Yes |
| User baseline features (typing averages) | Local SQLite | Yes |
| Challenge quality ratings (1-5 stars) | Local JSON (data/ratings.json) | No |

## Data We NEVER Collect

- **Individual keystrokes** or typed content — only aggregate metrics (WPM, error rates)
- **Browsing history** — only app/domain names and category time totals
- **Personal files, emails, messages, or documents**
- **Passwords or authentication tokens** (API keys stored in OS keychain)
- **Microphone, camera, or location data**
- **Contact lists, calendars, or system information**

## Telemetry

**Zero.** The application does not phone home. There is no analytics, no crash reporting, no usage tracking, and no network requests of any kind except:
- Optional API calls to Claude/OpenAI (if you provide API keys)
- Optional ArXiv/Semantic Scholar lookups (knowledge crawler, if enabled)
- Optional Garmin Connect data fetch (if you provide credentials)

All optional external connections are explicitly configurable and disabled by default.

## API Key Security

- API keys are stored in the **operating system's native keychain** (Windows Credential Manager / macOS Keychain)
- Keys are **never written to disk in plain text**
- Keys are **never included in data exports**
- Each API call to Claude/OpenAI sends only non-sensitive context metadata (time of day, fatigue score, activity category) — **no text content, keystroke data, or personal information**

## Your Rights

### Export Your Data
```bash
python -m src.main export
```
Exports all your locally stored data as human-readable JSON in `data/export.json`.

### Delete Your Data
```bash
python -m src.main delete
```
Permanently removes all stored data — usage logs, fatigue events, challenges, baselines, ratings. Confirmation required.

### Opt Out of Monitoring
Stop the daemon at any time (Ctrl+C or quit via system tray). No data is collected while the application is not running.

### Control What's Monitored
Edit `config/categories.json` to add, remove, or reclassify which applications are tracked. Edit `.env` to adjust intervention thresholds.

## Data Retention

Data is retained indefinitely on your device until you delete it. There is no automatic deletion. You control your data completely.

## Third-Party Dependencies

The browser extension (Chrome MV3) operates within Chrome's extension sandbox. It communicates with the desktop daemon via Chrome Native Messaging — no data is sent to Google or other third parties.

## Changes to This Policy

Since the application is fully open-source, any privacy-related changes are visible in the git history. The `SECOND-KNOWLEDGE-BRAIN.md` knowledge base contains domain research but no user data.

## Contact

This is an open-source project. Questions about privacy can be raised as GitHub issues on the project repository.
