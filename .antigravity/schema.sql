-- Antigravity Mnemosyne: Extended Schema (Phase 11.19.7 Sovereign)
-- Generated: 2026-05-10 [01:05 PM PT]
-- Auto-generated from runtime tables. Do not edit directly -- update cognition/mnemosyne stores instead.

-- =============================================================
-- 1. Rational Memory (Axis 10) - Governance & Agent Config
-- =============================================================

CREATE TABLE IF NOT EXISTS governance_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id VARCHAR(50) UNIQUE NOT NULL,
    agent_id VARCHAR(50) DEFAULT 'system',
    description TEXT NOT NULL,
    severity INTEGER DEFAULT 1,
    active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id VARCHAR(50) DEFAULT 'global',
    subject VARCHAR(255) NOT NULL,
    predicate VARCHAR(255),
    object TEXT NOT NULL,
    source VARCHAR(255),
    confidence FLOAT DEFAULT 1.0,
    last_verified DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_facts_agent ON facts(agent_id);

-- =============================================================
-- 2. Episodic Memory (Axis 1)
-- =============================================================

CREATE TABLE IF NOT EXISTS episodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(64) NOT NULL,
    agent_id VARCHAR(50) DEFAULT 'system',
    action VARCHAR(255) NOT NULL,
    detail TEXT,
    outcome VARCHAR(50) DEFAULT 'pending',
    tokens_used INTEGER DEFAULT 0,
    latency_ms FLOAT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_episodes_session ON episodes(session_id, created_at);

-- Event stream part of Episodic Memory
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(64) NOT NULL,
    seq_num INTEGER DEFAULT 0,
    event_type VARCHAR(100) NOT NULL,
    agent_id VARCHAR(50) DEFAULT 'system',
    payload TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id, created_at);

-- =============================================================
-- 3. Operational Memory (Axis 7) - Logging & Telemetry
-- =============================================================

CREATE TABLE IF NOT EXISTS operational_logs_v2 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    agent_id VARCHAR(50),
    tool_name VARCHAR(100),
    name TEXT,
    level TEXT,
    message TEXT
);

-- =============================================================
-- 4. Procedural Memory (Axis 2) - Tool Paths & Usage
-- =============================================================

CREATE TABLE IF NOT EXISTS tool_paths (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id VARCHAR(50) DEFAULT 'system',
    tool_name VARCHAR(100) NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    avg_latency_ms FLOAT DEFAULT 0,
    last_used DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);
CREATE INDEX IF NOT EXISTS idx_tool_paths_task ON tool_paths(task_type, success_count DESC);

-- =============================================================
-- 5. Goal Memory (Axis 3) - Future Planning
-- =============================================================

CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id VARCHAR(50) DEFAULT 'system',
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 3,
    parent_goal_id INTEGER,
    progress_pct FLOAT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME
);
CREATE INDEX IF NOT EXISTS idx_goals_active ON goals(status, priority);

-- =============================================================
-- 6. Meta-Cognition (Axis 8) - Self-Awareness
-- =============================================================

CREATE TABLE IF NOT EXISTS meta_cognition (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id VARCHAR(50) DEFAULT 'system',
    task TEXT,
    draft_quality FLOAT DEFAULT 0.5,
    critique_severity FLOAT DEFAULT 0.5,
    refinement_improvement FLOAT DEFAULT 0,
    num_iterations INTEGER DEFAULT 1,
    pattern_notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_experience (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id VARCHAR(50) NOT NULL,
    session_id VARCHAR(64),
    task_pattern VARCHAR(255),
    total_tasks INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    avg_quality FLOAT DEFAULT 0.5,
    best_model VARCHAR(100),
    best_temperature FLOAT DEFAULT 0.3,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_exp_agent ON agent_experience(agent_id);

-- agent_reliability lives in EXTERNAL DB: data/reliability.db (ReliabilityBase)
-- Managed by: cognition/mnemosyne/meta_cognition.py
CREATE TABLE IF NOT EXISTS agent_reliability (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id VARCHAR(50) NOT NULL UNIQUE,
    reliability_score FLOAT DEFAULT 1.0,
    total_violations INTEGER DEFAULT 0,
    last_violation_type VARCHAR(50),
    last_violation_at DATETIME,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================
-- 7. Efficiency (Axis 12) - Context Caching
-- =============================================================

CREATE TABLE IF NOT EXISTS context_cache (
    key TEXT PRIMARY KEY,
    content TEXT,
    expires_at FLOAT,
    created_at FLOAT,
    size_bytes INTEGER
);

-- =============================================================
-- 8. Creative/Tone (Axis 9) - Style Adaptation
-- =============================================================

CREATE TABLE IF NOT EXISTS tone_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(64) NOT NULL,
    tone VARCHAR(50),
    urgency FLOAT DEFAULT 0.5,
    verbosity FLOAT DEFAULT 0.5,
    original_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================
-- 9. Spatial (Axis 5) - Managed via src/lachesis/mapper/
-- =============================================================
CREATE TABLE IF NOT EXISTS spatial_modules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module_name VARCHAR(255) NOT NULL UNIQUE,
    file_path VARCHAR(512),
    line_count INTEGER DEFAULT 0,
    num_functions INTEGER DEFAULT 0,
    content_hash VARCHAR(64),
    last_indexed DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS spatial_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_module VARCHAR(255) NOT NULL,
    target_module VARCHAR(255) NOT NULL,
    relationship VARCHAR(50) DEFAULT 'imports',
    depth INTEGER DEFAULT 1
);

-- =============================================================
-- LanceDB Vector Schema Documentation (code-first, NOT SQLite)
-- Managed by: cognition/mnemosyne/semantic_store.py
-- Physical path: data/lancedb/
-- =============================================================
-- Table: semantic_memory.lance (Axis 6)
--   Fields: vector FLOAT[256], text TEXT, metadata JSON,
--           importance FLOAT, timestamp FLOAT, session_id VARCHAR(64)
-- =============================================================

-- =============================================================
-- 9B. Temporal (Axis 4) - migrated from LanceDB to SQLite (Phase 11.14)
-- Managed by: cognition/mnemosyne/temporal_store.py
-- Schema: stored in data/mnemosyne.db alongside other axes
-- =============================================================
-- CREATE TABLE IF NOT EXISTS temporal_metrics (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     timestamp REAL NOT NULL,
--     session_id TEXT NOT NULL,
--     event_type TEXT,
--     model_name TEXT,
--     tokens_used INTEGER DEFAULT 0,
--     latency_ms REAL DEFAULT 0.0,
--     vram_gb REAL DEFAULT 0.0,
--     metadata TEXT DEFAULT '{}'
-- );
-- CREATE INDEX IF NOT EXISTS idx_temp_session ON temporal_metrics(session_id, timestamp DESC);
-- =============================================================

-- =============================================================
-- 10. External Bridge (Axis 13) - OpenCode DB (READ-ONLY)
-- Managed by: src/architrave/opencode_store.py
-- Physical path: D:/opencode/opencode.db (configurable via $OPENCODE_HOME)
-- =============================================================
-- Table: session (read-only)
--   id TEXT PRIMARY KEY, project_id TEXT, slug TEXT, directory TEXT,
--   title TEXT, version TEXT, agent TEXT, model TEXT,
--   summary_additions INTEGER, summary_deletions INTEGER,
--   summary_files INTEGER, summary_diffs TEXT,
--   time_created INTEGER, time_updated INTEGER, ...
-- Table: message (read-only)
--   id TEXT PRIMARY KEY, session_id TEXT NOT NULL,
--   time_created INTEGER, time_updated INTEGER,
--   data TEXT (JSON message content)
-- =============================================================

-- =============================================================
-- 11. Knowledge & Entities (Axis 6 Extension)
-- =============================================================
CREATE TABLE IF NOT EXISTS entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,
    session_id VARCHAR(64),
    frequency INTEGER DEFAULT 1,
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, type)
);

-- =============================================================
-- 12. Semantic Relations (Axis 5 Extension)
-- =============================================================
CREATE TABLE IF NOT EXISTS semantic_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject VARCHAR(255) NOT NULL,
    predicate VARCHAR(100) NOT NULL,
    object VARCHAR(255) NOT NULL,
    session_id VARCHAR(64),
    confidence FLOAT DEFAULT 1.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================
-- 13. Reflective Insights (Axis 8 Extension)
-- =============================================================
CREATE TABLE IF NOT EXISTS reflections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    insight TEXT NOT NULL,
    category VARCHAR(50),
    session_id VARCHAR(64),
    agent_id VARCHAR(50) DEFAULT 'sophia',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================
-- 14. Failure Memory (Axis 8 Extension - Phase 11.19)
-- =============================================================
CREATE TABLE IF NOT EXISTS failure_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    error_type VARCHAR(100) NOT NULL,
    root_cause TEXT NOT NULL,
    prevention_rule TEXT NOT NULL,
    recurrence_count INTEGER DEFAULT 1,
    context_hash VARCHAR(16) NOT NULL UNIQUE,
    severity INTEGER DEFAULT 1,
    status VARCHAR(20) DEFAULT 'active', -- active, archived, promoted
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_failure_hash ON failure_memory(context_hash);
