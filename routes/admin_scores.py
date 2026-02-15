import math
from datetime import datetime
import os

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from supabase import create_client
from services.scores import score_from_attempts

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

admin_scores_bp = Blueprint("admin_scores", __name__)

ROWS_PER_PAGE = 10


@admin_scores_bp.route("/admin/scores", methods=["GET", "POST"])
@login_required
def manage_scores():

    if current_user.id != "admin":
        flash("Accès refusé", "error")
        return redirect(url_for("dashboard"))

    # ---------- POST actions ----------
    if request.method == "POST":
        action = request.form.get("action")

        # ➕ Ajouter
        if action == "add":
            attempts = int(request.form["attempts"])

            supabase.table("scores").insert({
                "date": request.form["date"],
                "username": request.form["username"],
                "attempts": attempts,
                "points": score_from_attempts(attempts),
            }).execute()

            flash("Score ajouté", "success")

        # ✏️ Modifier
        elif action == "edit":
            score_id = request.form["index"]
            attempts = int(request.form["attempts"])

            supabase.table("scores").update({
                "date": request.form["date"],
                "attempts": attempts,
                "points": score_from_attempts(attempts),
            }).eq("id", score_id).execute()

            flash("Score modifié", "success")

        # 🗑️ Supprimer
        elif action == "delete":
            score_id = request.form["id"]

            supabase.table("scores") \
                .delete() \
                .eq("id", score_id) \
                .execute()

            flash("Score supprimé", "success")

        return redirect(url_for("admin_scores.manage_scores"))

    # ---------- GET pagination ----------
    page = request.args.get("page", 1, type=int)

    start = (page - 1) * ROWS_PER_PAGE
    end = start + ROWS_PER_PAGE - 1

    # récupérer scores triés
    response = supabase.table("scores") \
        .select("*", count="exact") \
        .order("date", desc=True) \
        .order("username") \
        .range(start, end) \
        .execute()

    scores = response.data
    total_rows = response.count or 0
    total_pages = math.ceil(total_rows / ROWS_PER_PAGE)

    return render_template(
        "admin_scores.html",
        scores=scores,
        today=datetime.today().strftime("%Y-%m-%d"),
        page=page,
        total_pages=total_pages
    )
