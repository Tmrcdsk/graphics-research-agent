from __future__ import annotations

import sqlite3
from pathlib import Path

from app.storage.db import Database


def test_init_schema_migrates_existing_papers_table(tmp_path: Path) -> None:
    db_path = tmp_path / "old.sqlite3"
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            """
            CREATE TABLE papers (
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
            """
        )
        connection.execute(
            """
            INSERT INTO papers (
                arxiv_id,
                title,
                authors_json,
                abstract,
                categories_json,
                published_at,
                abs_url,
                title_hash,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "2606.00001",
                "Old arXiv Paper",
                "[]",
                "Rendering abstract",
                "[]",
                "2026-06-26T00:00:00+00:00",
                "https://arxiv.org/abs/2606.00001",
                "old-hash",
                "2026-06-26T00:00:00+00:00",
            ),
        )
        connection.commit()
    finally:
        connection.close()

    database = Database(db_path)
    try:
        database.init_schema()
        columns = database._paper_columns()
        row = database._connection.execute(
            "SELECT source_name, source_id FROM papers WHERE arxiv_id = ?",
            ("2606.00001",),
        ).fetchone()
    finally:
        database.close()

    assert "source_name" in columns
    assert "source_id" in columns
    assert row["source_name"] == "arxiv"
    assert row["source_id"] == "2606.00001"
