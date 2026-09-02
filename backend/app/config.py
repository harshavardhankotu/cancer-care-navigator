import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SQLite by default for local dev; set DATABASE_URL to a postgres:// or postgresql:// URL for production.
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

STORAGE_DIR = os.environ.get("STORAGE_DIR", os.path.join(BASE_DIR, "storage"))

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-secret-change-me-in-production-0123456789")
USING_DEFAULT_SECRET = "SECRET_KEY" not in os.environ
TOKEN_ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 72

# Never ship with a wildcard CORS policy on health data. Set ALLOWED_ORIGINS in prod.
ALLOWED_ORIGINS = [o.strip() for o in os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000"
).split(",") if o.strip()]

DISCLAIMER = ("This is not medical advice. It organizes your records and flags "
              "questions to raise with your treating oncologist.")
