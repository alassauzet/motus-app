from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from datetime import date
from auth import authenticate, User
from services.scores import upsert_score, monthly_leaderboard, daily_progress
from config import SCORES_FILE, USERS_FILE

app = Flask(__name__)
app.secret_key = "{{YOUR_SECRET_KEY}}"  # Render va le remplacer automatiquement

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.before_first_request
def init_storage():
    # Création automatique des CSV si absents
    if not USERS_FILE.exists():
        USERS_FILE.write_text("username,password_hash\n")
    if not SCORES_FILE.exists():
        SCORES_FILE.write_text("date,username,attempts,points\n")

@app.route("/", methods=["GET", "POST"])
@login_required
def dashboard():
    if request.method == "POST":
        attempts = int(request.form["attempts"])
        upsert_score(current_user.id, attempts)
        return redirect(url_for("dashboard"))

    today = date.today()
    leaderboard = monthly_leaderboard(today.year, today.month)
    progress = daily_progress(current_user.id, today.year, today.month)

    labels = [d.strftime("%d/%m") for d in progress.index]
    values = list(progress.values)

    return render_template(
        "dashboard.html",
        today=today,
        leaderboard=leaderboard,
        labels=labels,
        values=values
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = authenticate(
            request.form["username"],
            request.form["password"]
        )
        if user:
            login_user(user)
            return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run()
