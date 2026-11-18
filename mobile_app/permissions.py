"""Client-side permission checks for the Android application.

The authoritative source is the desktop database (or the LAN API).  This
module mirrors the same rules so the mobile UI and the offline fallback never
grant access based on job title alone:

- explicit grants in ``user_permissions`` (plus the legacy CSV column),
- ``X.manage`` implies the whole section,
- ``exports.data`` implies every ``*.export`` permission,
- superadmin bypass,
- no explicit grant means no access.
"""

from __future__ import annotations

from contextlib import closing

SECTION_PERMISSIONS = {
    "projects": (
        "projects.view", "projects.create", "projects.edit",
        "projects.delete", "projects.members", "projects.technical",
        "projects.export",
    ),
    "reports": (
        "reports.view", "reports.create", "reports.edit",
        "reports.delete", "reports.approve", "reports.export",
    ),
    "finance": (
        "finance.view", "finance.income.create", "finance.expense.create",
        "finance.expense.edit", "finance.expense.delete",
        "finance.reports_view", "finance.export", "finance.salaries",
    ),
    "invoices": (
        "invoices.view", "invoices.create", "invoices.edit",
        "invoices.delete", "invoices.approve", "invoices.export",
    ),
    "warehouse": (
        "warehouse.view", "warehouse.create", "warehouse.edit",
        "warehouse.delete", "warehouse.stock_in", "warehouse.stock_out",
        "warehouse.reports_view", "warehouse.export",
    ),
    "customers": (
        "customers.view", "customers.create", "customers.edit",
        "customers.delete", "customers.export",
    ),
    "timesheets": (
        "timesheets.view", "timesheets.create", "timesheets.edit",
        "timesheets.delete", "timesheets.approve", "timesheets.export",
    ),
    "materials": (
        "materials.view", "materials.create", "materials.edit",
        "materials.delete", "materials.approve", "materials.export",
    ),
    "files": (
        "files.view", "files.upload", "files.edit", "files.delete",
    ),
    "messages": ("messages.view", "messages.send"),
    "requests": (
        "requests.view", "requests.create", "requests.edit",
        "requests.approve", "requests.delete", "requests.export",
    ),
    "tasks": (
        "tasks.view", "tasks.create", "tasks.edit", "tasks.delete",
    ),
    "calendar": ("calendar.view", "calendar.manage"),
    "performance": (
        "performance.view", "performance.view_all", "performance.export",
    ),
    "sync": ("sync.view", "sync.manage"),
    "users": (
        "users.view", "users.create", "users.edit", "users.permissions",
        "users.disable", "users.sessions", "users.activity",
    ),
}

LEGACY_ALIASES = {
    "create_project": "projects.create",
    "edit_any_project": "projects.edit",
    "delete_project": "projects.delete",
    "view_all_projects": "projects.view",
    "create_report": "reports.create",
    "approve_reports": "reports.approve",
    "view_all_reports": "reports.view",
    "edit_expenses": "finance.expense.edit",
    "view_all_expenses": "finance.view",
    "manage_users": "users.view",
    "view_salaries": "finance.salaries",
    "export_data": "exports.data",
    "use_auto_timer": "timer.use",
}

GENERAL_PERMISSIONS = (
    "app.login", "home.view", "dashboard.view", "notifications.view",
    "global_search.use", "profile.view", "profile.edit",
    "settings.personal", "timer.use",
)

# فقط برای سازگاری با پایگاه‌داده‌های قدیمی که هنوز مهاجرت نشده‌اند.
LEGACY_ROLE_DEFAULTS = {
    "admin": None,  # همه مجوزها
    "engineer": (
        "home.view", "calendar.view", "projects.view", "reports.view",
        "timesheets.view", "materials.view", "finance.view", "files.view",
        "requests.view", "calculators.view", "sync.view",
        "settings.view", "settings.personal", "profile.view",
        "profile.edit", "notifications.view", "global_search.use",
        "app.login", "projects.create", "reports.create", "timer.use",
    ),
    "viewer": (
        "home.view", "calendar.view", "projects.view", "reports.view",
        "timesheets.view", "materials.view", "finance.view", "files.view",
        "requests.view", "calculators.view", "sync.view",
        "settings.view", "settings.personal", "profile.view",
        "profile.edit", "notifications.view", "global_search.use",
        "app.login",
    ),
}


def _row_value(user, key, default=None):
    try:
        value = user[key]
    except (KeyError, IndexError, TypeError):
        return default
    return default if value is None else value


def is_superadmin(user):
    value = _row_value(user, "is_superadmin")
    if value is None:
        # پایگاه‌داده قدیمی ستون is_superadmin ندارد.
        return str(_row_value(user, "role", "") or "") == "admin"
    try:
        return bool(int(value))
    except (TypeError, ValueError):
        return False


def _expand(keys):
    result = set()
    for raw in keys:
        key = str(raw or "").strip()
        if not key:
            continue
        mapped = LEGACY_ALIASES.get(key, key)
        result.add(mapped)
        if mapped.endswith(".manage"):
            section = mapped.split(".", 1)[0]
            result.update(SECTION_PERMISSIONS.get(section, ()))
            if section == "warehouse":
                result.add("warehouse.manage")
        if mapped == "exports.data":
            for values in SECTION_PERMISSIONS.values():
                result.update(
                    item for item in values if item.endswith(".export")
                )
        if mapped == "settings.manage":
            result.add("settings.personal")
        if mapped == "profile.edit":
            result.add("profile.view")
    return result


def _table_exists(connection, name):
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (name,),
    ).fetchone() is not None


def _column_names(connection, table):
    try:
        return {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}
    except Exception:
        return set()


def explicit_permissions(connection, user):
    username = str(_row_value(user, "username", "") or "")
    found = set()
    if _table_exists(connection, "user_permissions"):
        for row in connection.execute(
            "SELECT permission_key FROM user_permissions "
            "WHERE username = ? AND allowed = 1",
            (username,),
        ):
            found.add(row[0])
    legacy_csv = str(_row_value(user, "permissions", "") or "")
    found.update(part.strip() for part in legacy_csv.split(",") if part.strip())
    return found


def effective_permissions(connection, user):
    if not user:
        return set()
    if is_superadmin(user):
        return set(GENERAL_PERMISSIONS) | {
            item for values in SECTION_PERMISSIONS.values() for item in values
        }
    raw = explicit_permissions(connection, user)
    legacy_mode = not _table_exists(connection, "user_permissions")
    if not raw and legacy_mode:
        role = str(_row_value(user, "role", "") or "")
        defaults = LEGACY_ROLE_DEFAULTS.get(role)
        raw = set() if defaults is None else set(defaults)
    result = _expand(raw)
    if is_superadmin(user):
        result.update(GENERAL_PERMISSIONS)
    return result


def has_permission(connection, user, permission):
    if not user or not permission:
        return False
    if is_superadmin(user):
        return True
    key = LEGACY_ALIASES.get(permission, permission)
    effective = effective_permissions(connection, user)
    if key in effective:
        return True
    if key.endswith(".export") and "exports.data" in effective:
        return True
    section = key.split(".", 1)[0]
    return f"{section}.manage" in effective


def platform_allowed(user, platform="android"):
    column = {"windows": "platform_windows", "android": "platform_android"}.get(
        platform
    )
    if not column:
        return False
    value = _row_value(user, column)
    if value is None:
        # snapshot قدیمی؛ مدیر می‌تواند با نسخه تازه دسکتاپ محدود کند.
        return True
    try:
        return bool(int(value))
    except (TypeError, ValueError):
        return False


def account_active(user):
    active = _row_value(user, "active", 0)
    try:
        if not int(active or 0):
            return False
    except (TypeError, ValueError):
        return False
    status = _row_value(user, "account_status", "active")
    return status in (None, "", "active")
