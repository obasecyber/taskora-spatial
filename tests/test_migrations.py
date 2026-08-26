import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_migrations_generate_clean_database_sql():
    environment = os.environ.copy()
    environment["DATABASE_URL"] = "postgresql+psycopg://ci_user:ci_password@localhost:5432/ci_db"
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head", "--sql"],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "CREATE EXTENSION IF NOT EXISTS postgis" in result.stdout
    assert "CREATE EXTENSION IF NOT EXISTS vector" in result.stdout
    assert "002_m0_1_hardening" in result.stdout
    assert "CREATE TRIGGER audit_events_append_only" in result.stdout