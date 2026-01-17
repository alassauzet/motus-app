from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from services.users import update_password

profile_bp = Blueprint("profile", __name__)

@profile_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        old = request.form["old_password"]
        new = request.form["new_password"]
        confirm = request.form["confirm_password"]

        if new != confirm:
            flash("Les mots de passe ne correspondent pas", "error")
        else:
            ok, msg = update_password(current_user.id, old, new)
            flash(msg, "success" if ok else "error")
            if ok:
                return redirect(url_for("dashboard"))

    return render_template("change_password.html")
