from flask import Blueprint, abort, flash, g, redirect, render_template, request, session, url_for

from app.clients.auth import AuthClient
from app.clients.base import ServiceError
from app.middleware.auth import require_permission

bp = Blueprint("admin", __name__, url_prefix="/admin")
_client = AuthClient()


def _token() -> str:
    return session.get("access_token", "")


# ── Roles panel ───────────────────────────────────────────────────────────────


@bp.route("/roles")
@require_permission("users:roles:manage")
def roles():
    try:
        roles_list = _client.list_roles(_token())
    except ServiceError as exc:
        flash(f"Ошибка загрузки ролей: {exc.message}", "danger")
        roles_list = []
    return render_template("admin/roles.html", roles=roles_list)


@bp.route("/roles/new", methods=["POST"])
@require_permission("users:roles:manage")
def create_role():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip() or None
    try:
        _client.create_role({"name": name, "description": description, "permission_codes": []}, _token())
        flash(f"Роль «{name}» создана", "success")
    except ServiceError as exc:
        flash(f"Ошибка: {exc.message}", "danger")
    return redirect(url_for("admin.roles"))


@bp.route("/roles/<role_id>")
@require_permission("users:roles:manage")
def role_detail(role_id: str):
    try:
        role = _client.get_role(role_id, _token())
        perm_groups = _client.list_permissions_grouped(_token())
    except ServiceError as exc:
        flash(f"Ошибка: {exc.message}", "danger")
        return redirect(url_for("admin.roles"))

    assigned_codes = {p["code"] for p in role.get("permissions", [])}
    return render_template(
        "admin/role_detail.html",
        role=role,
        perm_groups=perm_groups,
        assigned_codes=assigned_codes,
    )


@bp.route("/roles/<role_id>/edit", methods=["POST"])
@require_permission("users:roles:manage")
def edit_role(role_id: str):
    data = {}
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    if name:
        data["name"] = name
    if description is not None:
        data["description"] = description or None
    try:
        _client.update_role(role_id, data, _token())
        flash("Роль обновлена", "success")
    except ServiceError as exc:
        flash(f"Ошибка: {exc.message}", "danger")
    return redirect(url_for("admin.role_detail", role_id=role_id))


@bp.route("/roles/<role_id>/permissions", methods=["POST"])
@require_permission("users:roles:manage")
def set_permissions(role_id: str):
    codes = request.form.getlist("permissions")
    try:
        _client.set_role_permissions(role_id, codes, _token())
        flash("Права роли обновлены", "success")
    except ServiceError as exc:
        flash(f"Ошибка: {exc.message}", "danger")
    return redirect(url_for("admin.role_detail", role_id=role_id))


@bp.route("/roles/<role_id>/delete", methods=["POST"])
@require_permission("users:roles:manage")
def delete_role(role_id: str):
    try:
        _client.delete_role(role_id, _token())
        flash("Роль удалена", "success")
    except ServiceError as exc:
        flash(f"Ошибка: {exc.message}", "danger")
    return redirect(url_for("admin.roles"))


# ── Users panel ───────────────────────────────────────────────────────────────


@bp.route("/users")
@require_permission("users:users:manage")
def users():
    try:
        users_list = _client.list_users(_token())
        roles_list = _client.list_roles(_token())
    except ServiceError as exc:
        flash(f"Ошибка загрузки: {exc.message}", "danger")
        users_list = []
        roles_list = []
    return render_template("admin/users.html", users=users_list, roles=roles_list)


@bp.route("/users/new", methods=["POST"])
@require_permission("users:users:manage")
def create_user():
    data = {
        "email": request.form.get("email", "").strip(),
        "full_name": request.form.get("full_name", "").strip(),
        "password": request.form.get("password", ""),
        "is_active": request.form.get("is_active") == "1",
    }
    role_id = request.form.get("role_id", "").strip()
    if role_id:
        data["role_id"] = role_id
    try:
        _client.create_user(data, _token())
        flash(f"Пользователь «{data['email']}» создан", "success")
    except ServiceError as exc:
        flash(f"Ошибка: {exc.message}", "danger")
    return redirect(url_for("admin.users"))


@bp.route("/users/<user_id>/edit", methods=["POST"])
@require_permission("users:users:manage")
def edit_user(user_id: str):
    data: dict = {}
    full_name = request.form.get("full_name", "").strip()
    role_id = request.form.get("role_id", "").strip()
    is_active = request.form.get("is_active")
    password = request.form.get("password", "").strip()

    if full_name:
        data["full_name"] = full_name
    if role_id:
        data["role_id"] = role_id
    if is_active is not None:
        data["is_active"] = is_active == "1"
    if password:
        data["password"] = password

    try:
        _client.update_user(user_id, data, _token())
        flash("Пользователь обновлён", "success")
    except ServiceError as exc:
        flash(f"Ошибка: {exc.message}", "danger")
    return redirect(url_for("admin.users"))


@bp.route("/users/<user_id>/delete", methods=["POST"])
@require_permission("users:users:manage")
def delete_user(user_id: str):
    try:
        _client.delete_user(user_id, _token())
        flash("Пользователь удалён", "success")
    except ServiceError as exc:
        flash(f"Ошибка: {exc.message}", "danger")
    return redirect(url_for("admin.users"))
