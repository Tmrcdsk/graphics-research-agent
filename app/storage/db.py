from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from app.config import Settings
from app.sources.models import PaperItem
from app.storage.models import InsertPaperResult, PublishLogRecord
from app.utils.time import utc_now_iso

SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS papers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        arxiv_id TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        authors_json TEXT NOT NULL,
        abstract TEXT NOT NULL,
        categories_json TEXT NOT NULL,
        published_at TEXT NOT NULL,
        updated_at TEXT,
        abs_url TEXT NOT NULL,
        pdf_url TEXT,
        title_hash TEXT NOT NULL,
        raw_json TEXT,
        created_at TEXT NOT NULL
    )
    """,
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_papers_abs_url ON papers(abs_url)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_papers_title_hash ON papers(title_hash)",
    """
    CREATE TABLE IF NOT EXISTS summaries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paper_id INTEGER NOT NULL,
        model_name TEXT NOT NULL,
        prompt_version TEXT NOT NULL,
        classification_json TEXT NOT NULL,
        summary_json TEXT NOT NULL,
        read_priority TEXT NOT NULL,
        relevance_score INTEGER,
        job_relevance_score INTEGER,
        created_at TEXT NOT NULL,
        FOREIGN KEY (paper_id) REFERENCES papers(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS publish_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paper_id INTEGER NOT NULL,
        channel TEXT NOT NULL,
        status TEXT NOT NULL,
        external_message_id TEXT,
        error TEXT,
        published_at TEXT NOT NULL,
        FOREIGN KEY (paper_id) REFERENCES papers(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS source_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_name TEXT NOT NULL,
        started_at TEXT NOT NULL,
        finished_at TEXT,
        status TEXT NOT NULL,
        fetched_count INTEGER DEFAULT 0,
        new_count INTEGER DEFAULT 0,
        candidate_count INTEGER DEFAULT 0,
        pushed_count INTEGER DEFAULT 0,
        error TEXT
    )
    """,
]


class Database:
    def __init__(self, database_path: Path) -> None:
        self.path = database_path
        if self.path.parent != Path(""):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.path)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")

    @classmethod
    def from_settings(cls, settings: Settings) -> Database:
        return cls(settings.database_path)

    def close(self) -> None:
        self._connection.close()

    def init_schema(self) -> None:
        with self._connection:
            for statement in SCHEMA_STATEMENTS:
                self._connection.execute(statement)

    def create_source_run(self, source_name: str) -> int:
        with self._connection:
            cursor = self._connection.execute(
                """
                INSERT INTO source_runs (source_name, started_at, status)
                VALUES (?, ?, ?)
                """,
                (source_name, utc_now_iso(), "running"),
            )
        return int(cursor.lastrowid)

    def finish_source_run(
        self,
        run_id: int,
        *,
        status: str,
        fetched_count: int,
        new_count: int,
        candidate_count: int,
        pushed_count: int,
        error: str | None = None,
    ) -> None:
        with self._connection:
            self._connection.execute(
                """
                UPDATE source_runs
                SET finished_at = ?,
                    status = ?,
                    fetched_count = ?,
                    new_count = ?,
                    candidate_count = ?,
                    pushed_count = ?,
                    error = ?
                WHERE id = ?
                """,
                (
                    utc_now_iso(),
                    status,
                    fetched_count,
                    new_count,
                    candidate_count,
                    pushed_count,
                    error,
                    run_id,
                ),
            )

    def insert_paper(self, paper: PaperItem) -> InsertPaperResult:
        existing_id = self.find_duplicate_paper_id(paper)
        if existing_id is not None:
            return InsertPaperResult(paper_id=existing_id, is_new=False)

        try:
            with self._connection:
                cursor = self._connection.execute(
                    """
                    INSERT INTO papers (
                        arxiv_id,
                        title,
                        authors_json,
                        abstract,
                        categories_json,
                        published_at,
                        updated_at,
                        abs_url,
                        pdf_url,
                        title_hash,
                        raw_json,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        paper.arxiv_id,
                        paper.title,
                        json.dumps(paper.authors, ensure_ascii=False),
                        paper.abstract,
                        json.dumps(paper.categories, ensure_ascii=False),
                        paper.published_at.isoformat(),
                        paper.updated_at.isoformat() if paper.updated_at else None,
                        paper.abs_url,
                        paper.pdf_url,
                        paper.title_hash,
                        (
                            json.dumps(paper.raw, ensure_ascii=False)
                            if paper.raw is not None
                            else None
                        ),
                        utc_now_iso(),
                    ),
                )
            return InsertPaperResult(paper_id=int(cursor.lastrowid), is_new=True)
        except sqlite3.IntegrityError:
            duplicate_id = self.find_duplicate_paper_id(paper)
            if duplicate_id is None:
                raise
            return InsertPaperResult(paper_id=duplicate_id, is_new=False)

    def find_duplicate_paper_id(self, paper: PaperItem) -> int | None:
        row = self._connection.execute(
            """
            SELECT id FROM papers
            WHERE arxiv_id = ? OR abs_url = ? OR title_hash = ?
            ORDER BY id ASC
            LIMIT 1
            """,
            (paper.arxiv_id, paper.abs_url, paper.title_hash),
        ).fetchone()
        return int(row["id"]) if row else None

    def save_summary(
        self,
        *,
        paper_id: int,
        model_name: str,
        prompt_version: str,
        classification: dict[str, Any],
        summary: dict[str, Any],
        read_priority: str,
        relevance_score: int | None,
        job_relevance_score: int | None,
    ) -> int:
        with self._connection:
            cursor = self._connection.execute(
                """
                INSERT INTO summaries (
                    paper_id,
                    model_name,
                    prompt_version,
                    classification_json,
                    summary_json,
                    read_priority,
                    relevance_score,
                    job_relevance_score,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    paper_id,
                    model_name,
                    prompt_version,
                    json.dumps(classification, ensure_ascii=False),
                    json.dumps(summary, ensure_ascii=False),
                    read_priority,
                    relevance_score,
                    job_relevance_score,
                    utc_now_iso(),
                ),
            )
        return int(cursor.lastrowid)

    def has_successful_publish(self, paper_id: int, channel: str) -> bool:
        row = self._connection.execute(
            """
            SELECT id FROM publish_logs
            WHERE paper_id = ? AND channel = ? AND status = 'success'
            LIMIT 1
            """,
            (paper_id, channel),
        ).fetchone()
        return row is not None

    def record_publish_log(
        self,
        *,
        paper_id: int,
        channel: str,
        status: str,
        external_message_id: str | None = None,
        error: str | None = None,
    ) -> int:
        with self._connection:
            cursor = self._connection.execute(
                """
                INSERT INTO publish_logs (
                    paper_id,
                    channel,
                    status,
                    external_message_id,
                    error,
                    published_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (paper_id, channel, status, external_message_id, error, utc_now_iso()),
            )
        return int(cursor.lastrowid)

    def count_rows(self, table_name: str) -> int:
        if table_name not in {"papers", "summaries", "publish_logs", "source_runs"}:
            raise ValueError(f"Unsupported table name: {table_name}")
        row = self._connection.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()
        return int(row["count"])

    def list_publish_logs(self) -> list[PublishLogRecord]:
        rows = self._connection.execute(
            """
            SELECT paper_id, channel, status, external_message_id, error
            FROM publish_logs
            ORDER BY id ASC
            """
        ).fetchall()
        return [
            PublishLogRecord(
                paper_id=int(row["paper_id"]),
                channel=str(row["channel"]),
                status=str(row["status"]),
                external_message_id=row["external_message_id"],
                error=row["error"],
            )
            for row in rows
        ]


def init_database(settings: Settings) -> Database:
    database = Database.from_settings(settings)
    database.init_schema()
    return database


def close_all(databases: Iterable[Database]) -> None:
    for database in databases:
        database.close()
