import locale
from datetime import date

from flask import Flask, render_template, request, redirect, url_for, g
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

from auth import authenticate, User
from config import SCORES_FILE, USERS_FILE
from routes.admin import admin_bp
from routes.profile import profile_bp
from services.scores import upsert_score, monthly_leaderboard, daily_progress_all

app = Flask(__name__)
app.secret_key = "{{YOUR_SECRET_KEY}}"  # Render va le remplacer automatiquement

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

# --- Register blueprints ---
app.register_blueprint(profile_bp)
app.register_blueprint(admin_bp)

try:
    locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_ALL, '')  # utilise la locale par défaut du système


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


# --- Initialisation compatible Flask 3.x ---
def ensure_files():
    """Créer les CSV s’ils n’existent pas"""
    if not USERS_FILE.exists():
        USERS_FILE.write_text("username,password_hash\n")
    if not SCORES_FILE.exists():
        SCORES_FILE.write_text("date,username,attempts,points\n")


@app.before_request
def init_storage():
    if not getattr(g, 'initialized', False):
        ensure_files()
        g.initialized = True


# ------------------------------------------

@app.route("/", methods=["GET", "POST"])
@login_required
def dashboard():
    if request.method == "POST":
        attempts = int(request.form["attempts"])
        upsert_score(current_user.id, attempts)
        return redirect(url_for("dashboard"))

    today = date.today()
    formatted_date = today.strftime("%d %B %Y")
    leaderboard = monthly_leaderboard(today.year, today.month)
    progress = daily_progress_all(today.year, today.month)

    labels = [d.strftime('%d/%m') for d in progress.index]

    total_users = len(progress.columns)

    datasets = []
    for i, user in enumerate(progress.columns):
        # Couleur unique par utilisateur
        hue = int(i * 360 / total_users)  # répartir les teintes sur le cercle HSL
        color = f"hsl({hue}, 70%, 60%)"
        datasets.append({
            "label": user,
            "data": progress[user].tolist(),
            "stepped": "after",
            "borderColor": color,
            "backgroundColor": "transparent",  # pas de remplissage
            "borderWidth": 2
        })

    return render_template(
        "dashboard.html",
        today=formatted_date,
        leaderboard=leaderboard,
        labels=labels,
        datasets=datasets
    )


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


if __name__ == "__main__":
    app.run()
