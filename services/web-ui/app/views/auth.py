from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.clients.auth import AuthClient
from app.clients.base import ServiceError

bp = Blueprint("auth", __name__, url_prefix="/auth")
_client = AuthClient()


@bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("access_token"):
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        try:
            data = _client.login(email, password)
            session["access_token"] = data["access_token"]
            session["user_email"] = email
            flash("Добро пожаловать!", "success")
            next_url = request.args.get("next") or url_for("dashboard.index")
            return redirect(next_url)
        except ServiceError as exc:
            if exc.status_code == 401:
                flash("Неверный email или пароль", "danger")
            elif exc.status_code == 403:
                flash("Аккаунт деактивирован", "danger")
            else:
                flash(f"Ошибка входа: {exc.message}", "danger")

    return render_template("auth/login.html")


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Вы вышли из системы", "info")
    return redirect(url_for("auth.login"))
