import os
from typing import Any

import psycopg


def get_database_url() -> str:
    return os.getenv(
        "DATABASE_URL",
        "postgresql://support_user:support_pass@localhost:5432/support_ai",
    )


def init_db() -> None:
    with psycopg.connect(get_database_url(), autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_logs (
                    id BIGSERIAL PRIMARY KEY,
                    model TEXT NOT NULL,
                    user_message TEXT NOT NULL,
                    assistant_message TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )


def insert_chat_log(model: str, user_message: str, assistant_message: str) -> None:
    with psycopg.connect(get_database_url(), autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO chat_logs (model, user_message, assistant_message)
                VALUES (%s, %s, %s)
                """,
                (model, user_message, assistant_message),
            )


def fetch_recent_logs(limit: int = 20) -> list[dict[str, Any]]:
    with psycopg.connect(get_database_url(), autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, model, user_message, assistant_message, created_at
                FROM chat_logs
                ORDER BY id DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "model": row[1],
            "user_message": row[2],
            "assistant_message": row[3],
            "created_at": row[4].isoformat(),
        }
        for row in rows
    ]


def delete_chat_log(log_id: int) -> bool:
    with psycopg.connect(get_database_url(), autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM chat_logs WHERE id = %s", (log_id,))
            return cur.rowcount > 0
