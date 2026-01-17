import os
from pathlib import Path

# Si une variable d'environnement DATA_DIR est définie, on l'utilise
# Sinon, on reste dans un dossier 'motus_data' à la racine du projet
DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).parent / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)  # crée le dossier si nécessaire

USERS_FILE = DATA_DIR / "users.csv"
SCORES_FILE = DATA_DIR / "scores.csv"
WORDS_FILE = DATA_DIR / "words.csv"
