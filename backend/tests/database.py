import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.pool import NullPool

TEST_DATABASE = "local_ai_assistant_test"
BACKEND_ROOT = Path(__file__).resolve().parents[1]


def db_server_up() -> bool:
    database_url = os.environ.get("DATABASE_URL", "")
    if not database_url:
        return False
    admin = make_url(database_url).set(database="postgres")
    engine = create_engine(admin, poolclass=NullPool, connect_args={"connect_timeout": 3})
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
    finally:
        engine.dispose()


def ensure_test_database() -> str:
    source = make_url(os.environ["DATABASE_URL"])
    admin = create_engine(
        source.set(database="postgres"),
        poolclass=NullPool,
        connect_args={"connect_timeout": 3},
    )
    with admin.connect() as connection:
        connection.execution_options(isolation_level="AUTOCOMMIT")
        result = connection.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": TEST_DATABASE},
        )
        if not result.fetchone():
            connection.execute(text(f'CREATE DATABASE "{TEST_DATABASE}" ENCODING \'UTF8\''))
    admin.dispose()
    return source.set(database=TEST_DATABASE).render_as_string(hide_password=False)


def migrate(database_url: str) -> None:
    env = os.environ.copy()
    env["DATABASE_URL"] = database_url
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_ROOT,
        env=env,
        check=True,
    )


def create_test_engine() -> Engine:
    database_url = ensure_test_database()
    migrate(database_url)
    return create_engine(database_url, pool_pre_ping=True)
