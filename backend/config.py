import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./osint_app.db")
FABRIC_PATH = os.getenv("FABRIC_PATH", "fabric")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-v4-flash")
OPENROUTER_VENDOR = os.getenv("OPENROUTER_VENDOR", "OpenRouter")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_API_BASE_URL = os.getenv("OPENROUTER_API_BASE_URL", "https://openrouter.ai/api/v1")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "200"))
YOUTUBE_COOKIES_BROWSER = os.getenv("YOUTUBE_COOKIES_BROWSER", "")