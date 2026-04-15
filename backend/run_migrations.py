#!/usr/bin/env python3
from __future__ import annotations

import os
import re
from pathlib import Path

import psycopg
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent
MIGRATIONS_DIR = BACKEND_DIR / "migrations" / "postgres"
SCHEMA_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def load_environment() -> tuple[str, str]:
    # Load from backend/.env first, then project-root .env (same pattern used across repo).
    load_dotenv(BACKEND_DIR / ".env")
    load_dotenv(ROOT_DIR / ".env", override=False)

    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set in environment/.env")

    schema = os.getenv("DATABASE_SCHEMA", "public").strip() or "public"
    if not SCHEMA_NAME_RE.match(schema):
        raise RuntimeError(f"Unsafe DATABASE_SCHEMA value: {schema!r}")
    return database_url, schema


def normalize_postgres_url(database_url: str) -> str:
    if database_url.startswith("postgresql+psycopg://"):
        return database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    if database_url.startswith("postgresql://"):
        return database_url
    raise RuntimeError(
        "Only PostgreSQL URLs are supported by this migration runner. "
        "Set DATABASE_URL to a PostgreSQL connection string."
    )


def ensure_migrations_table(cur: psycopg.Cursor, schema: str) -> None:
    cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
    cur.execute(
        f"""
        CREATE TABLE IF NOT EXISTS "{schema}".schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )


def apply_migration(cur: psycopg.Cursor, schema: str, migration_path: Path) -> None:
    version = migration_path.name
    cur.execute(
        f'SELECT 1 FROM "{schema}".schema_migrations WHERE version = %s',
        (version,),
    )
    if cur.fetchone():
        print(f"SKIP   {version}")
        return

    sql_text = migration_path.read_text(encoding="utf-8").replace("__SCHEMA__", schema)
    cur.execute(sql_text)
    cur.execute(
        f'INSERT INTO "{schema}".schema_migrations (version) VALUES (%s)',
        (version,),
    )
    print(f"APPLY  {version}")


def main() -> None:
    database_url, schema = load_environment()
    postgres_url = normalize_postgres_url(database_url)

    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not migration_files:
        print("No migration files found.")
        return

    with psycopg.connect(postgres_url) as conn:
        with conn.cursor() as cur:
            ensure_migrations_table(cur, schema)
            for migration in migration_files:
                apply_migration(cur, schema, migration)
        conn.commit()

    print("Migrations complete.")


if __name__ == "__main__":
    main()
