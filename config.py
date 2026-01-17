from pathlib import Path

# Version Free Plan : CSV dans /tmp (données volatiles)
DATA_DIR = Path("/tmp/motus_data")
DATA_DIR.mkdir(exist_ok=True)

USERS_FILE = DATA_DIR / "users.csv"
SCORES_FILE = DATA_DIR / "scores.csv"
WORDS_FILE = DATA_DIR / "words.csv"
