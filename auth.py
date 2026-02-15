import os

from flask_login import UserMixin
from werkzeug.security import check_password_hash
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


class User(UserMixin):
    def __init__(self, username):
        self.id = username


def get_user(username):
    response = (
        supabase.table("users")
        .select("username, password_hash")
        .eq("username", username)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    row = response.data[0]
    return {
        "username": row["username"],
        "password_hash": row["password_hash"]
    }


def authenticate(username, password):

    # === Admin fallback pour debug / POC ===
    if username == "admin" and password == "admin":
        return User(username)

    # === Auth Supabase ===
    user = get_user(username)

    if user and check_password_hash(user["password_hash"], password):
        return User(username)

    return None
