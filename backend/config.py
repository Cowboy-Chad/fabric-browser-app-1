import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./osint_app.db")
FABRIC_PATH = os.getenv("FABRIC_PATH", "fabric")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-v4-flash")
OPENROUTER_VENDOR = os.getenv("OPENROUTER_VENDOR", "OpenRouter")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "200"))
YOUTUBE_COOKIES_BROWSER = os.getenv("YOUTUBE_COOKIES_BROWSER", "")