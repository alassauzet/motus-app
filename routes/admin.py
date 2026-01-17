from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
import pandas as pd
from werkzeug.security import generate_password_hash
from config import USERS_FILE

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/admin/users", methods=["GET", "POST"])
@login_required
def manage_users():
    # Seulement admin
    if current_user.id != "admin":
        flash("Accès refusé", "error")
        return redirect(url_for("dashboard"))

    df = pd.read_csv(USERS_FILE) if USERS_FILE.exists() else pd.DataFrame(columns=["username","password_hash"])

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in df.username.values:
            flash("Utilisateur déjà existant", "error")
        else:
            df = pd.concat([df, pd.DataFrame([{
                "username": username,
                "password_hash": generate_password_hash(password)
            }])], ignore_index=True)
            df.to_csv(USERS_FILE, index=False)
            flash(f"Utilisateur {username} créé", "success")
            return redirect(url_for("admin.manage_users"))

    return render_template("admin_users.html", users=df["username"].tolist())
