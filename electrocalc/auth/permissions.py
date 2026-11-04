"""سیستم مجوزها (دسترسی‌ها)."""

from electrocalc.data.database import get_connection


# لیست همه مجوزها
PERMISSIONS = {
    "create_project": "ساخت پروژه جدید",
    "edit_any_project": "ویرایش همه پروژه‌ها",
    "delete_project": "حذف پروژه",
    "view_all_projects": "دیدن همه پروژه‌ها",
    "create_report": "ثبت گزارش",
    "approve_reports": "تأیید/رد گزارش‌ها",
    "view_all_reports": "دیدن همه گزارش‌ها",
    "edit_expenses": "ویرایش هزینه‌ها",
    "view_all_expenses": "دیدن همه هزینه‌ها",
    "manage_users": "مدیریت کاربران",
    "view_salaries": "دیدن حقوق و دستمزد",
    "export_data": "خروجی گرفتن (PDF/Excel)",
    "use_auto_timer": "استفاده از تایمر خودکار ورود/خروج",
}

# مجوزهای پیش‌فرض برای هر نقش
DEFAULTS = {
    "admin": list(PERMISSIONS.keys()),
    "engineer": ["create_project", "create_report", "use_auto_timer"],
    "viewer": [],
}


def get_user_permissions(user):
    """لیست مجوزهای فعال یک کاربر."""
    if not user:
        return []
    if user["role"] == "admin":
        return list(PERMISSIONS.keys())

    perms = ""
    try:
        if "permissions" in user.keys():
            perms = user["permissions"] or ""
    except Exception:
        perms = ""

    if perms.strip():
        return [p.strip() for p in perms.split(",") if p.strip()]
    return DEFAULTS.get(user["role"], [])


def has_permission(user, permission: str) -> bool:
    """آیا کاربر این مجوز رو داره؟"""
    return permission in get_user_permissions(user)


def set_permissions(username: str, perms_list) -> bool:
    """ذخیره مجوزهای کاربر."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE users SET permissions = ? WHERE username = ?",
            (",".join(perms_list), username),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()