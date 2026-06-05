# Digital Fasting Companion — PyInstaller Build Specification
# Build command: pyinstaller digital-fasting.spec

# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config/schema.sql', 'config/'),
        ('config/categories.json', 'config/'),
        ('src/intervention/challenge_pool.json', 'src/intervention/'),
        ('src/ui/overlay.html', 'src/ui/'),
        ('src/ui/dashboard.html', 'src/ui/'),
        ('src/ui/settings.html', 'src/ui/'),
        ('.env.example', '.'),
    ],
    hiddenimports=[
        'pynput',
        'psutil',
        'cryptography',
        'pydantic',
        'pydantic_settings',
        'httpx',
        'keyring',
        'apscheduler',
        'src.config.settings',
        'src.storage.local_db',
        'src.monitor.screen_time',
        'src.monitor.keystroke',
        'src.detector.fatigue_model',
        'src.detector.ml_fatigue_detector',
        'src.detector.feature_pipeline',
        'src.detector.baseline_collector',
        'src.intervention.lock_engine',
        'src.agent.router',
        'src.agent.static_pool',
        'src.agent.claude_backend',
        'src.agent.openai_backend',
        'src.agent.ollama_backend',
        'src.knowledge.crawler',
        'src.knowledge.relevance_scorer',
        'src.biometrics.garmin_backend',
        'src.biometrics.apple_health',
        'src.scheduler',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'jupyter',
        'notebook',
        'IPython',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='digital-fasting-companion',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='browser-extension/icons/icon128.png',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='digital-fasting-companion',
)
