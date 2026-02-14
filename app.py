from datetime import date
from babel.dates import format_date
import os

from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

from auth import authenticate, User
from routes.admin import admin_bp
from routes.admin_scores import admin_scores_bp
from routes.profile import profile_bp

# --- Supabase client ---
from supabase import create_client
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]  # clé backend
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Import des services Supabase-ready ---
from services import scores, users  # modules que nous avons convertis

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-key")

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

# --- Register blueprints ---
app.register_blueprint(profile_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(admin_scores_bp)


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


# ------------------------------------------
@app.route("/health")
def health():
    return "ok", 200


# ------------------------------------------
@app.route("/", methods=["GET", "POST"])
@login_required
def dashboard():
    if request.method == "POST":
        attempts = int(request.form["attempts"])
        scores.upsert_score(current_user.id, attempts)
        return redirect(url_for("dashboard"))

    today = date.today()
    formatted_date = format_date(today, format="d MMMM y", locale="fr_FR")

    leaderboard = scores.monthly_leaderboard(today.year, today.month)
    progress = scores.daily_progress_all(today.year, today.month)

    labels = [d.strftime('%d/%m') for d in progress.index] if not progress.empty else []

    total_users = len(progress.columns) if not progress.empty else 0
    user_colors = {}
    datasets = []
    for i, user in enumerate(progress.columns if not progress.empty else []):
        hue = int(i * 360 / total_users)
        color = f"hsl({hue}, 70%, 60%)"
        user_colors[user] = color
        datasets.append({
            "label": user,
            "data": progress[user].tolist(),
            "borderColor": color,
            "backgroundColor": "transparent",
            "borderWidth": 2
        })

    player_attempts_today = scores.get_player_attempts(current_user.id, today)
    user_games_this_month = scores.monthly_games_played(today)
    user_trends = scores.compute_user_trends(progress)

    return render_template(
        "dashboard.html",
        today=formatted_date,
        leaderboard=leaderboard,
        labels=labels,
        datasets=datasets,
        player_attempts_today=player_attempts_today,
        user_colors=user_colors,
        user_games_this_month=user_games_this_month,
        user_trends=user_trends
    )


# ------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        user = authenticate(
            request.form["username"],
            request.form["password"]
        )
        if user:
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            error = "Identifiants incorrects"

    return render_template("login.html", error=error)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# Optionnel : endpoint pour changer le mot de passe via users.py
@app.route("/update-password", methods=["POST"])
@login_required
def update_password():
    old = request.form.get("old_password")
    new = request.form.get("new_password")
    success, message = users.update_password(current_user.id, old, new)
    return {"success": success, "message": message}


if __name__ == "__main__":
    app.run()
