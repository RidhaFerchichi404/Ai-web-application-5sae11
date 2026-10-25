import os

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg2://test:test@127.0.0.1:5432/local_ai_assistant",
)
os.environ.setdefault("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
os.environ.setdefault("OLLAMA_CHAT_MODEL", "test-chat")
os.environ.setdefault("OLLAMA_EMBEDDING_MODEL", "test-embed")
os.environ.setdefault("MAX_FILE_SIZE_MB", "25")
os.environ.setdefault("UPLOAD_DIRECTORY", "./storage/uploads")

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from app.db.session import get_db
from app.main import app
from tests.database import create_test_engine, db_server_up


@pytest.fixture(scope="session")
def test_engine():
    if not db_server_up():
        pytest.skip("PostgreSQL is unreachable")
    engine = create_test_engine()
    yield engine
    engine.dispose()


@pytest.fixture
def db(test_engine):
    factory = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)

    def override():
        session = factory()
        try:
            yield session
        finally:
            session.close()

    def clean(session: Session) -> None:
        session.execute(
            text(
                "TRUNCATE document_chunks, documents, messages, conversations, users"
                " RESTART IDENTITY CASCADE"
            )
        )
        session.commit()

    app.dependency_overrides[get_db] = override
    probe = factory()
    clean(probe)
    yield probe
    clean(probe)
    probe.close()
    app.dependency_overrides.pop(get_db, None)
