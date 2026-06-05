-- Digital Fasting Companion Database Schema
-- SQLite with SQLCipher encryption

-- ============================================
-- USAGE SESSIONS
-- ============================================
CREATE TABLE IF NOT EXISTS usage_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL UNIQUE,
    app_name TEXT NOT NULL,
    category TEXT NOT NULL,
    start_time INTEGER NOT NULL,  -- Unix timestamp
    end_time INTEGER,          -- Unix timestamp
    duration_seconds INTEGER DEFAULT 0,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_sessions_start_time ON usage_sessions(start_time);
CREATE INDEX IF NOT EXISTS idx_sessions_category ON usage_sessions(category);


-- ============================================
-- FATIGUE EVENTS
-- ============================================
CREATE TABLE IF NOT EXISTS fatigue_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL UNIQUE,
    event_type TEXT NOT NULL,  -- 'tier1', 'tier2', 'tier3'
    fatigue_score REAL NOT NULL,
    session_id TEXT,            -- FK to usage_sessions.session_id
    trigger_category TEXT,
    trigger_time INTEGER NOT NULL,
    resolved_time INTEGER,
    resolution_type TEXT,       -- 'challenge_completed', 'timeout', 'manual'
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_fatigue_trigger_time ON fatigue_events(trigger_time);
CREATE INDEX IF NOT EXISTS idx_fatigue_event_type ON fatigue_events(event_type);


-- ============================================
-- CHALLENGES
-- ============================================
CREATE TABLE IF NOT EXISTS challenges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    challenge_id TEXT NOT NULL UNIQUE,
    event_id TEXT,             -- FK to fatigue_events.event_id
    category TEXT NOT NULL,   -- 'physical', 'creative', 'social', 'introspective'
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    source TEXT NOT NULL,     -- 'static', 'ollama', 'claude', 'openai'
    prompt TEXT,              -- Generation prompt if LLM-generated
    time_limit_seconds INTEGER DEFAULT 900,
    completed_at INTEGER,
    rating INTEGER,         -- 1-5 star rating
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_challenges_event_id ON challenges(event_id);
CREATE INDEX IF NOT EXISTS idx_challenges_category ON challenges(category);


-- ============================================
-- RECOVERY LOG
-- ============================================
CREATE TABLE IF NOT EXISTS recovery_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL UNIQUE,  -- FK to fatigue_events.event_id
    challenge_id TEXT,             -- FK to challenges.challenge_id
    start_time INTEGER NOT NULL,
    end_time INTEGER,
    quality_score REAL,            -- Post-recovery quality assessment
    notes TEXT,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_recovery_event_id ON recovery_log(event_id);


-- ============================================
-- USER BASELINE
-- ============================================
CREATE TABLE IF NOT EXISTS user_baseline (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feature_name TEXT NOT NULL,
    feature_value REAL NOT NULL,
    std_dev REAL DEFAULT 0,
    sample_count INTEGER DEFAULT 0,
    last_updated INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    UNIQUE(feature_name)
);

-- Insert default baseline features
INSERT OR IGNORE INTO user_baseline (feature_name, feature_value, std_dev, sample_count) VALUES
    ('typing_wpm', 40.0, 10.0, 0),
    ('error_rate', 0.05, 0.02, 0),
    ('backspace_ratio', 0.08, 0.03, 0),
    ('session_duration_min', 30.0, 15.0, 0),
    ('app_switch_rate', 5.0, 2.0, 0),
    ('hour_of_day', 12.0, 4.0, 0),
    ('hrv_score', 50.0, 15.0, 0);


-- ============================================
-- APP CATEGORIES
-- ============================================
CREATE TABLE IF NOT EXISTS app_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_pattern TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    user_defined INTEGER DEFAULT 0,  -- 1 if user customized
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);

-- Default categories
INSERT OR IGNORE INTO app_categories (app_pattern, category) VALUES
    -- AI Tools
    ('chatgpt', 'ai_tools'),
    ('claude', 'ai_tools'),
    ('copilot', 'ai_tools'),
    ('bard', 'ai_tools'),
    ('gemini', 'ai_tools'),
    ('perplexity', 'ai_tools'),
    ('cursor', 'ai_tools'),
    ('windsurf', 'ai_tools'),
    ('llama', 'ai_tools'),
    ('ollama', 'ai_tools'),
    
    -- Social Media
    ('facebook', 'social_media'),
    ('twitter', 'social_media'),
    ('x.com', 'social_media'),
    ('instagram', 'social_media'),
    ('tiktok', 'social_media'),
    ('youtube', 'social_media'),
    ('reddit', 'social_media'),
    ('linkedin', 'social_media'),
    ('discord', 'social_media'),
    ('slack', 'social_media'),
    
    -- Productive
    ('code', 'productive'),
    ('vscode', 'productive'),
    ('sublime', 'productive'),
    ('notion', 'productive'),
    ('obsidian', 'productive'),
    ('evernote', 'productive'),
    ('calendar', 'productive'),
    ('mail', 'productive'),
    
    -- Entertainment
    ('spotify', 'entertainment'),
    ('netflix', 'entertainment'),
    ('twitch', 'entertainment'),
    ('steam', 'entertainment'),
    ('epic', 'entertainment');


-- ============================================
-- SETTINGS
-- ============================================
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    value TEXT,
    updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);

-- ============================================
-- ML MODEL CHECKPOINTS
-- ============================================
CREATE TABLE IF NOT EXISTS ml_checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    checkpoint_id TEXT NOT NULL UNIQUE,
    model_type TEXT NOT NULL,  -- 'fatigue_detector', etc
    model_data BLOB NOT NULL,   -- Serialized model (joblib)
    feature_names TEXT NOT NULL, -- JSON array of feature names
    metrics_json TEXT,         -- JSON of training metrics
    sample_count INTEGER DEFAULT 0,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);


-- ============================================
-- KNOWLEDGE CRAWL LOG
-- ============================================
CREATE TABLE IF NOT EXISTS knowledge_crawl_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crawl_id TEXT NOT NULL UNIQUE,
    source TEXT NOT NULL,      -- 'arxiv', 'huggingface', 'semantic_scholar'
    papers_found INTEGER DEFAULT 0,
    papers_added INTEGER DEFAULT 0,
    run_status TEXT NOT NULL,    -- 'success', 'error', 'partial'
    error_message TEXT,
    executed_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);

-- Create triggers for updated_at
CREATE TRIGGER IF NOT EXISTS update_settings_at
AFTER UPDATE ON settings
BEGIN
    UPDATE settings SET updated_at = strftime('%s', 'now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_baseline_at
AFTER UPDATE ON user_baseline
BEGIN
    UPDATE user_baseline SET last_updated = strftime('%s', 'now') WHERE id = NEW.id;
END;
