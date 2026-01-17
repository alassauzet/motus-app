from pathlib import Path

DATA_DIR = Path("/var/data")
DATA_DIR.mkdir(exist_ok=True)

USERS_FILE = DATA_DIR / "users.csv"
SCORES_FILE = DATA_DIR / "scores.csv"
WORDS_FILE = DATA_DIR / "words.csv"
