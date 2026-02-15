import os

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from supabase import create_client

admin_bp = Blueprint("admin", __name__)

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


@admin_bp.route("/admin/users", methods=["GET", "POST"])
@login_required
def manage_users():

    # Accès admin uniquement
    if current_user.id != "admin":
        flash("Accès refusé", "error")
        return redirect(url_for("dashboard"))

    # ---------- POST actions ----------
    if request.method == "POST":
        action = request.form.get("action")

        # ➕ Ajouter utilisateur
        if action == "add":
            username = request.form["username"]
            password = request.form["password"]

            existing = supabase.table("users") \
                .select("username") \
                .eq("username", username) \
                .execute()

            if existing.data:
                flash("Utilisateur déjà existant", "error")
            else:
                supabase.table("users").insert({
                    "username": username,
                    "password_hash": generate_password_hash(password)
                }).execute()

                flash(f"Utilisateur {username} créé", "success")

        # 🗑️ Supprimer utilisateur
        elif action == "delete":
            username = request.form["username"]

            if username == "admin":
                flash("Impossible de supprimer admin", "error")
            else:
                supabase.table("users") \
                    .delete() \
                    .eq("username", username) \
                    .execute()

                flash(f"Utilisateur {username} supprimé", "success")

        # 🔁 Reset mot de passe
        elif action == "reset_password":
            username = request.form["username"]
            new_password = request.form["new_password"]

            supabase.table("users") \
                .update({
                    "password_hash": generate_password_hash(new_password)
                }) \
                .eq("username", username) \
                .execute()

            flash(f"Mot de passe réinitialisé pour {username}", "success")

        return redirect(url_for("admin.manage_users"))

    # ---------- GET ----------
    response = supabase.table("users") \
        .select("username") \
        .order("username") \
        .execute()

    users = [u["username"] for u in response.data]

    return render_template(
        "admin_users.html",
        users=users
    )
