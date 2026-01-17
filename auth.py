import pandas as pd
from flask_login import UserMixin
from werkzeug.security import check_password_hash
from config import USERS_FILE

class User(UserMixin):
    def __init__(self, username):
        self.id = username

def get_user(username):
    df = pd.read_csv(USERS_FILE)
    row = df[df.username == username]
    if row.empty:
        return None
    return {
        "username": username,
        "password_hash": row.iloc[0]["password_hash"]
    }

def authenticate(username, password):
    # === POC Prototype Free Plan ===
    if username == "admin" and password == "admin":
        return User(username)
    
    # === Logique originale avec CSV ===
    user = get_user(username)
    if user and check_password_hash(user["password_hash"], password):
        return User(username)
    
    return None
