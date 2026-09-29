# config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env into environment variables
load_dotenv()

# ---------- Project paths ----------
PROJECT_ROOT = Path(__file__).resolve().parent
SCRAPE_DIR = PROJECT_ROOT / "scrape"
DATA_DIR = PROJECT_ROOT / "data"
SRC_DIR = PROJECT_ROOT / "src"
RAW_CSV = SCRAPE_DIR / "smartphones.csv"


# ---------- Database (AWS RDS) ----------
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")


# ---------- Fail fast if something is missing ----------
def validate_config():
    required = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASS"]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise EnvironmentError(f"Missing env vars: {missing}")
    print("Config loaded successfully.")


if __name__ == "__main__":
    validate_config()