-- sudo-patch SQLite 스키마 (docs/spec.md "DB")

CREATE TABLE IF NOT EXISTS sessions (
    id              TEXT PRIMARY KEY,
    packages_json   TEXT NOT NULL DEFAULT '[]',
    excluded_json   TEXT NOT NULL DEFAULT '[]',
    os              TEXT,
    os_version      TEXT,
    python_version  TEXT,
    capacity_n      INTEGER,
    first_date      TEXT,
    window_start    TEXT,
    window_end      TEXT,
    interval_days   INTEGER,
    weekdays        TEXT,
    weekly_count    INTEGER,
    week_interval   INTEGER,
    last_message    TEXT,
    last_answer     TEXT,
    last_plan_json  TEXT,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS plans (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id    TEXT NOT NULL,
    round_no      INTEGER NOT NULL,
    date          TEXT NOT NULL,
    window_start  TEXT,
    window_end    TEXT,
    items_json    TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'planned',
    done_at       TEXT,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);

-- 실행 로그: INSERT·조회·세션 단위 삭제만. 수정하지 않는다 (F3014)
CREATE TABLE IF NOT EXISTS events (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id    TEXT NOT NULL,
    seq           INTEGER NOT NULL,
    type          TEXT NOT NULL,
    payload_json  TEXT NOT NULL,
    created_at    TEXT NOT NULL,
    UNIQUE (session_id, seq)
);

CREATE INDEX IF NOT EXISTS idx_events_session ON events (session_id, seq);
CREATE INDEX IF NOT EXISTS idx_plans_date ON plans (date);

-- 캘린더 (심화 F3023, 로컬 구현체). source: user(직접 넣은 일정) / sudo-patch(확정 계획에서 등록)
CREATE TABLE IF NOT EXISTS calendar_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    date        TEXT NOT NULL,
    start_time  TEXT,
    end_time    TEXT,
    source      TEXT NOT NULL DEFAULT 'user',
    plan_id     INTEGER,
    created_at  TEXT NOT NULL,
    owner       TEXT              -- 공개 모드에서 일정 주인(세션). 로컬은 NULL (spec v1.24)
);

CREATE INDEX IF NOT EXISTS idx_calendar_date ON calendar_events (date);
