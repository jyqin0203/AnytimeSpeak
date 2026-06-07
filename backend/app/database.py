import sqlite3
import os
from pathlib import Path

DB_DIR = Path(__file__).parent.parent / "data"
DB_PATH = Path(os.environ.get("ANYTIMESPEAK_DB_PATH", DB_DIR / "anytimespeak.db"))

_CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS practice_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    session_id TEXT NOT NULL UNIQUE,
    scenario_id TEXT NOT NULL,
    scenario_title TEXT NOT NULL,
    story_intro TEXT,
    story_intro_zh TEXT,
    story_intro_en TEXT,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    score INTEGER,
    overall_score INTEGER,
    summary TEXT,
    summary_json TEXT,
    provider TEXT NOT NULL DEFAULT 'mock',
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES practice_sessions(session_id)
);

CREATE TABLE IF NOT EXISTS feedbacks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    message_id TEXT,
    user_message TEXT,
    feedback_json TEXT,
    score INTEGER,
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES practice_sessions(session_id)
);
"""


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        _migrate_legacy_users_table(conn)
        conn.executescript(_CREATE_TABLES_SQL)
        _ensure_practice_session_columns(conn)
        _repair_practice_session_user_fk(conn)


def _migrate_legacy_users_table(conn: sqlite3.Connection) -> None:
    table = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'users'"
    ).fetchone()
    if table is None:
        return

    columns = {row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()}
    if {"username", "password_hash"}.issubset(columns):
        return

    legacy_rows = conn.execute("SELECT id, display_name, created_at FROM users").fetchall()
    conn.execute("PRAGMA foreign_keys=OFF")
    conn.execute("ALTER TABLE users RENAME TO users_legacy_guest")
    conn.execute(
        """CREATE TABLE users (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )"""
    )

    used_usernames: set[str] = set()
    for row in legacy_rows:
        base = "".join(ch.lower() for ch in str(row["display_name"]).strip() if ch.isalnum()) or "legacy"
        username = base[:44]
        suffix = 1
        while username in used_usernames:
            suffix += 1
            username = f"{base[:40]}{suffix}"
        used_usernames.add(username)
        conn.execute(
            "INSERT INTO users (id, username, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (row["id"], username, "legacy_guest_password_disabled", row["created_at"]),
        )

    conn.execute("DROP TABLE users_legacy_guest")
    conn.execute("PRAGMA foreign_keys=ON")


def _ensure_practice_session_columns(conn: sqlite3.Connection) -> None:
    table = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'practice_sessions'"
    ).fetchone()
    if table is None:
        return

    columns = {row["name"] for row in conn.execute("PRAGMA table_info(practice_sessions)").fetchall()}
    migrations = {
        "story_intro": "ALTER TABLE practice_sessions ADD COLUMN story_intro TEXT",
        "score": "ALTER TABLE practice_sessions ADD COLUMN score INTEGER",
        "summary": "ALTER TABLE practice_sessions ADD COLUMN summary TEXT",
    }
    for column, sql in migrations.items():
        if column not in columns:
            conn.execute(sql)


def _repair_practice_session_user_fk(conn: sqlite3.Connection) -> None:
    table = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'practice_sessions'"
    ).fetchone()
    if table is None:
        return

    foreign_keys = conn.execute("PRAGMA foreign_key_list(practice_sessions)").fetchall()
    user_fk_targets = [row["table"] for row in foreign_keys if row["from"] == "user_id"]
    if user_fk_targets == ["users"]:
        return

    conn.execute("PRAGMA foreign_keys=OFF")
    conn.execute(
        """CREATE TABLE practice_sessions_rebuilt (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            session_id TEXT NOT NULL UNIQUE,
            scenario_id TEXT NOT NULL,
            scenario_title TEXT NOT NULL,
            story_intro TEXT,
            story_intro_zh TEXT,
            story_intro_en TEXT,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            score INTEGER,
            overall_score INTEGER,
            summary TEXT,
            summary_json TEXT,
            provider TEXT NOT NULL DEFAULT 'mock',
            FOREIGN KEY (user_id) REFERENCES users(id)
        )"""
    )
    conn.execute(
        """INSERT INTO practice_sessions_rebuilt
           (id, user_id, session_id, scenario_id, scenario_title,
            story_intro, story_intro_zh, story_intro_en, started_at, ended_at,
            score, overall_score, summary, summary_json, provider)
           SELECT id, user_id, session_id, scenario_id, scenario_title,
                  story_intro, story_intro_zh, story_intro_en, started_at, ended_at,
                  score, overall_score, summary, summary_json, provider
           FROM practice_sessions"""
    )
    conn.execute("DROP TABLE practice_sessions")
    conn.execute("ALTER TABLE practice_sessions_rebuilt RENAME TO practice_sessions")
    conn.execute("PRAGMA foreign_keys=ON")
