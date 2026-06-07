import json
import hashlib
import hmac
import os
from datetime import datetime, timezone
from uuid import uuid4

from app.database import get_connection
from app.history_schemas import (
    FeedbackRecord,
    MessageRecord,
    SaveSessionRequest,
    SessionDetail,
    SessionListItem,
    UserCredentialsRequest,
    UserResponse,
)

_PBKDF2_ITERATIONS = 120_000


def _normalize_username(username: str) -> str:
    return username.strip().lower()


def _hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${_PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations_raw, salt_hex, digest_hex = stored_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iterations_raw)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
    except (ValueError, TypeError):
        return False

    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual, expected)


def register_user(request: UserCredentialsRequest) -> UserResponse:
    user_id = f"user_{uuid4().hex[:12]}"
    username = _normalize_username(request.username)
    created_at = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO users (id, username, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (user_id, username, _hash_password(request.password), created_at),
        )
    return UserResponse(
        user_id=user_id,
        username=username,
        created_at=created_at,
    )


def login_user(request: UserCredentialsRequest) -> UserResponse | None:
    username = _normalize_username(request.username)
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, username, password_hash, created_at FROM users WHERE username = ?",
            (username,),
        ).fetchone()
    if row is None or not _verify_password(request.password, row["password_hash"]):
        return None
    return UserResponse(
        user_id=row["id"],
        username=row["username"],
        created_at=row["created_at"],
    )


def get_user(user_id: str) -> UserResponse | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, username, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    if row is None:
        return None
    return UserResponse(
        user_id=row["id"],
        username=row["username"],
        created_at=row["created_at"],
    )


def save_practice_session(request: SaveSessionRequest) -> SessionListItem:
    now = datetime.now(timezone.utc).isoformat()
    summary_json_str = json.dumps(request.summary, ensure_ascii=False) if request.summary else None

    overall_score = request.overall_score
    if overall_score is None and request.scores:
        raw = request.scores.get("overall") or request.scores.get("综合")
        if raw is not None:
            overall_score = int(raw)

    summary_preview: str | None = None
    if request.summary:
        for key in ("summary", "overallPerformance", "overall_performance"):
            val = request.summary.get(key)
            if val:
                summary_preview = str(val)[:120]
                break

    with get_connection() as conn:
        conn.execute(
            """INSERT INTO practice_sessions
               (id, user_id, session_id, scenario_id, scenario_title,
                story_intro_zh, story_intro_en, started_at, ended_at,
                overall_score, summary_json, provider)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(session_id) DO UPDATE SET
                 ended_at = excluded.ended_at,
                 overall_score = excluded.overall_score,
                 summary_json = excluded.summary_json,
                 provider = excluded.provider""",
            (
                f"ps_{uuid4().hex[:12]}",
                request.user_id,
                request.session_id,
                request.scenario_id,
                request.scenario_title,
                request.story_intro_zh,
                request.story_intro_en,
                now,
                now,
                overall_score,
                summary_json_str,
                request.provider,
            ),
        )
        conn.execute("DELETE FROM messages WHERE session_id = ?", (request.session_id,))
        conn.execute("DELETE FROM feedbacks WHERE session_id = ?", (request.session_id,))

        for msg in request.messages:
            conn.execute(
                "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                (request.session_id, msg.role, msg.content, now),
            )

        for fb in request.feedbacks:
            conn.execute(
                """INSERT INTO feedbacks
                   (session_id, user_message, feedback_json, score, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    request.session_id,
                    fb.user_message,
                    json.dumps(fb.feedback_json, ensure_ascii=False) if fb.feedback_json else None,
                    fb.score,
                    now,
                ),
            )

    return SessionListItem(
        session_id=request.session_id,
        scenario_id=request.scenario_id,
        scenario_title=request.scenario_title,
        started_at=now,
        overall_score=overall_score,
        summary_preview=summary_preview,
        provider=request.provider,
    )


def list_user_sessions(user_id: str, limit: int = 20) -> list[SessionListItem]:
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT session_id, scenario_id, scenario_title, started_at,
                      overall_score, summary_json, provider
               FROM practice_sessions
               WHERE user_id = ?
               ORDER BY started_at DESC
               LIMIT ?""",
            (user_id, limit),
        ).fetchall()

    items: list[SessionListItem] = []
    for row in rows:
        summary_preview: str | None = None
        if row["summary_json"]:
            try:
                summary = json.loads(row["summary_json"])
                for key in ("summary", "overallPerformance", "overall_performance"):
                    val = summary.get(key)
                    if val:
                        summary_preview = str(val)[:120]
                        break
            except Exception:
                pass

        items.append(
            SessionListItem(
                session_id=row["session_id"],
                scenario_id=row["scenario_id"],
                scenario_title=row["scenario_title"],
                started_at=row["started_at"],
                overall_score=row["overall_score"],
                summary_preview=summary_preview,
                provider=row["provider"],
            )
        )

    return items


def get_session_detail(session_id: str) -> SessionDetail | None:
    with get_connection() as conn:
        row = conn.execute(
            """SELECT session_id, scenario_id, scenario_title, story_intro_zh, story_intro_en,
                      started_at, ended_at, overall_score, summary_json, provider
               FROM practice_sessions WHERE session_id = ?""",
            (session_id,),
        ).fetchone()

        if row is None:
            return None

        msg_rows = conn.execute(
            "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()

        fb_rows = conn.execute(
            "SELECT user_message, feedback_json, score FROM feedbacks WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()

    summary_json = None
    if row["summary_json"]:
        try:
            summary_json = json.loads(row["summary_json"])
        except Exception:
            pass

    messages = [MessageRecord(role=r["role"], content=r["content"]) for r in msg_rows]

    feedbacks: list[FeedbackRecord] = []
    for fb in fb_rows:
        feedback_json = None
        if fb["feedback_json"]:
            try:
                feedback_json = json.loads(fb["feedback_json"])
            except Exception:
                pass
        feedbacks.append(
            FeedbackRecord(
                user_message=fb["user_message"],
                feedback_json=feedback_json,
                score=fb["score"],
            )
        )

    return SessionDetail(
        session_id=row["session_id"],
        scenario_id=row["scenario_id"],
        scenario_title=row["scenario_title"],
        story_intro_zh=row["story_intro_zh"],
        story_intro_en=row["story_intro_en"],
        started_at=row["started_at"],
        ended_at=row["ended_at"],
        overall_score=row["overall_score"],
        summary_json=summary_json,
        provider=row["provider"],
        messages=messages,
        feedbacks=feedbacks,
    )
