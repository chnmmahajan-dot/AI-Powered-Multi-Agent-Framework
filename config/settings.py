from pathlib import Path


# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Application configuration
BASE_URL = "http://127.0.0.1:8000"

# Demo application credentials
USERNAME = "admin"
PASSWORD = "password123"

# Project directories
REQUIREMENTS_FILE = PROJECT_ROOT / "user_stories" / "requirements.xlsx"
GENERATED_TESTS_DIR = PROJECT_ROOT / "generated_tests"
REPORTS_DIR = PROJECT_ROOT / "reports"
LOGS_DIR = PROJECT_ROOT / "logs"