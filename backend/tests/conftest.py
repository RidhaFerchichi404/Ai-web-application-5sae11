import os

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault(
    "DATABASE_URL",
    "mysql+pymysql://test:test@127.0.0.1:3306/local_ai_assistant",
)
os.environ.setdefault("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
os.environ.setdefault("OLLAMA_CHAT_MODEL", "test-chat")
os.environ.setdefault("OLLAMA_EMBEDDING_MODEL", "test-embed")
os.environ.setdefault("MAX_FILE_SIZE_MB", "25")
os.environ.setdefault("UPLOAD_DIRECTORY", "./storage/uploads")
