import os
from werkzeug.security import check_password_hash, generate_password_hash
from supabase import create_client
import pandas as pd

# --- Supabase client ---
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]  # clé backend
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def update_password(username, old_password, new_password):
    """Met à jour le mot de passe de l'utilisateur"""
    # Récupérer l'utilisateur depuis Supabase
    res = supabase.table("users").select("password_hash").eq("username", username).execute()
    
    if not res.data:
        return False, "Utilisateur introuvable"

    current_hash = res.data[0]["password_hash"]

    if not check_password_hash(current_hash, old_password):
        return False, "Mot de passe actuel incorrect"

    # Générer le nouveau hash
    new_hash = generate_password_hash(new_password)

    # Update dans Supabase
    supabase.table("users").update({"password_hash": new_hash}).eq("username", username).execute()

    return True, "Mot de passe mis à jour"


def create_user(username, password):
    """Crée un nouvel utilisateur avec hash de mot de passe"""
    # Vérifier si l'utilisateur existe déjà
    res = supabase.table("users").select("*").eq("username", username).execute()
    if res.data:
        return False, "Utilisateur déjà existant"

    password_hash = generate_password_hash(password)
    supabase.table("users").insert({
        "username": username,
        "password_hash": password_hash
    }).execute()

    return True, "Utilisateur créé"
