# ADR-001: Desktop Framework Selection

**Status:** Accepted  
**Date:** 2026-06-05  
**Deciders:** Digital Fasting Team  

---

## Context

The digital-fasting-companion requires a cross-platform desktop application with:
- System tray integration (background daemon)
- Full-screen overlay capability (challenge display)
- OS-level access (firewall rules, window minimization, process monitoring)
- WebView for HTML/CSS/JS UI rendering (dashboard, overlay)
- Windows 10/11 + macOS 13+ target platforms

---

## Decision

**Python-based daemon with HTML/JS overlays served locally.**

### What we chose

| Layer | Technology |
|-------|-----------|
| Core backend | Python 3.11+ with all logic in `src/` |
| System tray | pystray (Python) |
| UI rendering | Local HTML files served via simple HTTP server |
| Overlay trigger | `webbrowser.open()` or spawned browser window |
| Desktop packaging | PyInstaller (Windows .exe) + py2app (macOS .app) |

### What we rejected

| Option | Reason for rejection |
|--------|---------------------|
| **Tauri 2.0** (Rust + WebView) | Adds Rust toolchain complexity. Tight integration needed between Python monitoring modules and Rust frontend via IPC. Over-engineering for Phase 0–1. |
| **Electron v32** | Heavy (~200MB+ bundled). Overkill for a mostly-headless monitoring daemon. Poor resource profile for 24/7 background daemon. |
| **Pure Python + tkinter/Qt** | Native Python GUIs are ugly and have poor API surface for modern overlay UIs. HTML/CSS gives us far more flexibility. |

### Fallback path

If the HTML/JS overlay approach proves insufficient for production UX, we can adopt **Tauri 2.0** in Phase 3+ by exposing the Python backend as a local HTTP API that Tauri's Rust core calls. This requires no change to the Python monitoring/detection code — only the UI layer.

---

## Consequences

**Positive:**
- Zero JavaScript build tooling required — just plain HTML/CSS/JS files
- Full access to Python ecosystem (psutil, pynput, scikit-learn)
- Lightweight — daemon uses <50MB RAM idle, <100MB with ML loaded
- Single language stack for Phase 0–1 development velocity
- Easy to iterate: change HTML, refresh, see result

**Negative:**
- No native app store distribution path without packaging (solved by PyInstaller/py2app)
- Browser-based overlay may not feel fully "native"
- System tray implementation varies across platforms (pystray handles this)
- Deep OS integration (Win32 API, macOS AppKit) requires Python bridges

---

## Re-evaluation triggers

Re-evaluate Tauri 2.0 if:
1. Startup time becomes unacceptable (>2s cold start)
2. Browser overlay UX proves insufficient in user testing
3. Mobile companion app requires shared Rust core

---

*This ADR follows the Architecture Decision Record format.*
