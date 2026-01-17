import pandas as pd
from werkzeug.security import check_password_hash, generate_password_hash
from config import USERS_FILE

def update_password(username, old_password, new_password):
    df = pd.read_csv(USERS_FILE) if USERS_FILE.exists() else pd.DataFrame(columns=["username","password_hash"])

    mask = df.username == username
    if not mask.any():
        return False, "Utilisateur introuvable"

    current_hash = df.loc[mask, "password_hash"].iloc[0]
    if not check_password_hash(current_hash, old_password):
        return False, "Mot de passe actuel incorrect"

    df.loc[mask, "password_hash"] = generate_password_hash(new_password)
    df.to_csv(USERS_FILE, index=False)
    return True, "Mot de passe mis à jour"
