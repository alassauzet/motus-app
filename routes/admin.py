from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
import pandas as pd
from werkzeug.security import generate_password_hash
from config import USERS_FILE

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/admin/users", methods=["GET", "POST"])
@login_required
def manage_users():
    # Accès admin uniquement
    if current_user.id != "admin":
        flash("Accès refusé", "error")
        return redirect(url_for("dashboard"))

    # Chargement des utilisateurs
    if USERS_FILE.exists():
        df = pd.read_csv(USERS_FILE)
    else:
        df = pd.DataFrame(columns=["username", "password_hash"])

    if request.method == "POST":
        action = request.form.get("action")

        # ➕ Ajout utilisateur
        if action == "add":
            username = request.form["username"]
            password = request.form["password"]

            if username in df.username.values:
                flash("Utilisateur déjà existant", "error")
            else:
                df = pd.concat(
                    [
                        df,
                        pd.DataFrame([{
                            "username": username,
                            "password_hash": generate_password_hash(password)
                        }])
                    ],
                    ignore_index=True
                )
                df.to_csv(USERS_FILE, index=False)
                flash(f"Utilisateur {username} créé", "success")

        # 🗑️ Suppression utilisateur
        elif action == "delete":
            username = request.form["username"]

            if username == "admin":
                flash("Impossible de supprimer l’utilisateur admin", "error")
            elif username not in df.username.values:
                flash("Utilisateur introuvable", "error")
            else:
                df = df[df.username != username]
                df.to_csv(USERS_FILE, index=False)
                flash(f"Utilisateur {username} supprimé", "success")

        # 🔁 Reset mot de passe
        elif action == "reset_password":
            username = request.form["username"]
            new_password = request.form["new_password"]

            if username not in df.username.values:
                flash("Utilisateur introuvable", "error")
            else:
                df.loc[df.username == username, "password_hash"] = \
                    generate_password_hash(new_password)
                df.to_csv(USERS_FILE, index=False)
                flash(f"Mot de passe réinitialisé pour {username}", "success")

        return redirect(url_for("admin.manage_users"))

    return render_template(
        "admin_users.html",
        users=df["username"].tolist()
    )
