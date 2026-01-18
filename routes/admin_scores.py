import math
from datetime import datetime

import pandas as pd
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from config import SCORES_FILE
from services.scores import load_scores, score_from_attempts, LOCK

admin_scores_bp = Blueprint("admin_scores", __name__)

# Nombre de lignes par page
ROWS_PER_PAGE = 10


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
                date = pd.to_datetime(request.form["date"])
                attempts = int(request.form["attempts"])
                points_str = request.form.get("points", "")
                points = int(points_str) if points_str.isdigit() else score_from_attempts(attempts)
                df.loc[idx, ["date", "attempts", "points"]] = [date, attempts, points]
                flash("Score modifié", "success")

            # 🗑️ Supprimer
            elif action == "delete":
                df = df.drop(index=int(request.form["index"])).reset_index(drop=True)
                flash("Score supprimé", "success")

            df.to_csv(SCORES_FILE, index=False)
            return redirect(url_for("admin_scores.manage_scores"))

    # Pagination GET
    page = request.args.get("page", 1, type=int)
    df = df.reset_index()

    # 🔹 Trier du plus récent au plus ancien
    df.sort_values(by=["date", "username"], ascending=[False, True], inplace=True)

    total_rows = len(df)
    total_pages = math.ceil(total_rows / ROWS_PER_PAGE)
    start = (page - 1) * ROWS_PER_PAGE
    end = start + ROWS_PER_PAGE
    df_page = df.iloc[start:end]

    return render_template(
        "admin_scores.html",
        scores=df_page.to_dict(orient="records"),
        today=datetime.today().strftime("%Y-%m-%d"),
        page=page,
        total_pages=total_pages
    )
