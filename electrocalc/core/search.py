"""جستجوی سراسری در همه اطلاعات."""

from electrocalc.data.database import get_connection


def search_all(query, limit=10):
    """
    جستجو در همه جدول‌ها.
    خروجی: دیکشنری {دسته: لیست نتایج}
    """
    if not query or len(query.strip()) < 2:
        return {}

    q = f"%{query.strip()}%"
    results = {}

    conn = get_connection()
    cur = conn.cursor()

    # ---- پروژه‌ها ----
    try:
        cur.execute("""
            SELECT id, name, customer FROM projects
            WHERE name LIKE ? OR customer LIKE ? OR description LIKE ?
            LIMIT ?
        """, (q, q, q, limit))
        rows = [{"id": r["id"], "title": r["name"],
                 "subtitle": r["customer"] or ""} for r in cur.fetchall()]
        if rows:
            results["📁 پروژه‌ها"] = rows
    except Exception:
        pass

    # ---- کاربران ----
    try:
        cur.execute("""
            SELECT id, username, full_name, role FROM users
            WHERE username LIKE ? OR full_name LIKE ? OR phone LIKE ?
            LIMIT ?
        """, (q, q, q, limit))
        rows = []
        for r in cur.fetchall():
            role_fa = {"admin": "مدیر", "engineer": "مهندس",
                       "viewer": "ناظر"}.get(r["role"], r["role"])
            rows.append({"id": r["id"],
                         "title": r["full_name"] or r["username"],
                         "subtitle": f"@{r['username']}  —  {role_fa}"})
        if rows:
            results["👥 کاربران"] = rows
    except Exception:
        pass

    # ---- گزارش‌ها ----
    try:
        cur.execute("""
            SELECT r.id, r.title, r.author, p.name AS project_name
            FROM reports r
            LEFT JOIN projects p ON p.id = r.project_id
            WHERE r.title LIKE ? OR r.description LIKE ?
            LIMIT ?
        """, (q, q, limit))
        rows = [{"id": r["id"], "title": r["title"],
                 "subtitle": f"{r['author']}  —  {r['project_name'] or 'بدون پروژه'}"}
                for r in cur.fetchall()]
        if rows:
            results["📝 گزارش‌ها"] = rows
    except Exception:
        pass

    # ---- هزینه‌ها ----
    try:
        cur.execute("""
            SELECT e.id, e.title, e.amount, p.name AS project_name
            FROM expenses e
            LEFT JOIN projects p ON p.id = e.project_id
            WHERE e.title LIKE ? OR e.description LIKE ?
            LIMIT ?
        """, (q, q, limit))
        rows = [{"id": r["id"], "title": r["title"],
                 "subtitle": f"{r['amount']:,.0f} تومان  —  {r['project_name'] or '-'}"}
                for r in cur.fetchall()]
        if rows:
            results["💰 هزینه‌ها"] = rows
    except Exception:
        pass

    # ---- مصالح ----
    try:
        cur.execute("""
            SELECT m.id, m.name, m.total_price, p.name AS project_name
            FROM materials m
            LEFT JOIN projects p ON p.id = m.project_id
            WHERE m.name LIKE ? OR m.description LIKE ?
            LIMIT ?
        """, (q, q, limit))
        rows = [{"id": r["id"], "title": r["name"],
                 "subtitle": f"{r['total_price']:,.0f} تومان  —  {r['project_name'] or '-'}"}
                for r in cur.fetchall()]
        if rows:
            results["🔧 مصالح"] = rows
    except Exception:
        pass

    # ---- پیام‌ها ----
    try:
        cur.execute("""
            SELECT id, subject, sender, body FROM messages
            WHERE subject LIKE ? OR body LIKE ?
            LIMIT ?
        """, (q, q, limit))
        rows = [{"id": r["id"], "title": r["subject"] or "(بدون موضوع)",
                 "subtitle": f"از {r['sender']}: {r['body'][:50] if r['body'] else ''}"}
                for r in cur.fetchall()]
        if rows:
            results["💬 پیام‌ها"] = rows
    except Exception:
        pass

    # ---- فایل‌ها ----
    try:
        cur.execute("""
            SELECT id, title, uploaded_by FROM files
            WHERE title LIKE ? OR description LIKE ?
            LIMIT ?
        """, (q, q, limit))
        rows = [{"id": r["id"], "title": r["title"],
                 "subtitle": f"آپلود: {r['uploaded_by'] or '-'}"}
                for r in cur.fetchall()]
        if rows:
            results["📎 فایل‌ها"] = rows
    except Exception:
        pass

    # ---- ساعات کار ----
    try:
        cur.execute("""
            SELECT t.id, t.username, t.work_date, t.hours, p.name AS project_name
            FROM timesheets t
            LEFT JOIN projects p ON p.id = t.project_id
            WHERE t.username LIKE ? OR t.description LIKE ?
            LIMIT ?
        """, (q, q, limit))
        rows = [{"id": r["id"], "title": f"{r['username']} - {r['hours']:.1f} ساعت",
                 "subtitle": f"{r['work_date'] or ''}  —  {r['project_name'] or '-'}"}
                for r in cur.fetchall()]
        if rows:
            results["⏰ ساعات کار"] = rows
    except Exception:
        pass

    conn.close()
    return results