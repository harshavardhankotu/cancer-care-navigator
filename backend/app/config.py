import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SQLite by default for local dev; set DATABASE_URL to a postgres:// URL for production.
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

STORAGE_DIR = os.environ.get("STORAGE_DIR", os.path.join(BASE_DIR, "storage"))

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-secret-change-me-in-production-0123456789")
TOKEN_ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 72

DISCLAIMER = ("This is not medical advice. It organizes your records and flags "
              "questions to raise with your treating oncologist.")
