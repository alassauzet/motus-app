from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
import pandas as pd

from config import SCORES_FILE
from scores import load_scores, score_from_attempts, LOCK

admin_scores_bp = Blueprint("admin_scores", __name__)


@admin_scores_bp.route("/admin/scores", methods=["GET", "POST"])
@login_required
def manage_scores():
    # Admin only
    if current_user.id != "admin":
        flash("Accès refusé", "error")
        return redirect(url_for("dashboard"))

    with LOCK:
        df = load_scores()

        if request.method == "POST":
            action = request.form.get("action")

            # ➕ Ajouter
            if action == "add":
                df = pd.concat([
                    df,
                    pd.DataFrame([{
                        "date": pd.to_datetime(request.form["date"]),
                        "username": request.form["username"],
                        "attempts": int(request.form["attempts"]),
                        "points": score_from_attempts(int(request.form["attempts"]))
                    }])
                ], ignore_index=True)
                flash("Score ajouté", "success")

            # ✏️ Modifier
            elif action == "edit":
                idx = int(request.form["index"])
                attempts = int(request.form["attempts"])
                df.loc[idx, ["date", "attempts", "points"]] = [
                    pd.to_datetime(request.form["date"]),
                    attempts,
                    score_from_attempts(attempts)
                ]
                flash("Score modifié", "success")

            # 🗑️ Supprimer
            elif action == "delete":
                df = df.drop(index=int(request.form["index"])).reset_index(drop=True)
                flash("Score supprimé", "success")

            df.to_csv(SCORES_FILE, index=False)
            return redirect(url_for("admin_scores.manage_scores"))

    df = df.reset_index()

    return render_template(
        "admin_scores.html",
        scores=df.to_dict(orient="records"),
        today=datetime.today().strftime("%Y-%m-%d")
    )
