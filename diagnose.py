"""اسکریپت تشخیص باگ‌ها و مشکل پایگاه داده."""

import sys
import traceback
from pathlib import Path

# اضافه کردن مسیر پروژه
sys.path.insert(0, str(Path(__file__).resolve().parent))


def section(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_imports():
    section("۱) تست import ماژول‌ها")
    modules = [
        "electrocalc.config.constants",
        "electrocalc.config.themes",
        "electrocalc.config.settings",
        "electrocalc.data.database",
        "electrocalc.auth.users",
        "electrocalc.auth.permissions",
        "electrocalc.core.ohm",
        "electrocalc.core.power",
        "electrocalc.core.voltage_drop",
        "electrocalc.core.ampacity",
        "electrocalc.core.fuse",
        "electrocalc.core.motor",
        "electrocalc.core.units",
        "electrocalc.core.projects",
        "electrocalc.core.reports",
        "electrocalc.core.management",
        "electrocalc.core.company",
        "electrocalc.core.settings",
        "electrocalc.core.audit",
        "electrocalc.core.health",
        "electrocalc.core.backup",
        "electrocalc.core.notifications",
        "electrocalc.core.timer",
        "electrocalc.ui.main_window",
        "electrocalc.ui.login_window",
        "electrocalc.ui.scrollable_frame",
        "electrocalc.ui.change_password_dialog",
        "electrocalc.ui.profile_dialog",
        "electrocalc.ui.permissions_dialog",
        "electrocalc.ui.notifications_panel",
        "electrocalc.utils.avatar",
        "electrocalc.utils.logger",
    ]
    errors = []
    for m in modules:
        try:
            __import__(m)
            print(f"  ✅ {m}")
        except Exception as e:
            print(f"  ❌ {m}  →  {e}")
            errors.append((m, e))
    return errors


def test_tabs():
    section("۲) تست تب‌های UI")
    tabs = [
        ("electrocalc.ui.tabs.home_tab", "HomeTab"),
        ("electrocalc.ui.tabs.ohm_tab", "OhmTab"),
        ("electrocalc.ui.tabs.power_tab", "PowerTab"),
        ("electrocalc.ui.tabs.voltage_drop_tab", "VoltageDropTab"),
        ("electrocalc.ui.tabs.ampacity_tab", "AmpacityTab"),
        ("electrocalc.ui.tabs.fuse_tab", "FuseTab"),
        ("electrocalc.ui.tabs.motor_tab", "MotorTab"),
        ("electrocalc.ui.tabs.units_tab", "UnitsTab"),
        ("electrocalc.ui.tabs.projects_tab", "ProjectsTab"),
        ("electrocalc.ui.tabs.reports_tab", "ReportsTab"),
        ("electrocalc.ui.tabs.timesheet_tab", "TimesheetTab"),
        ("electrocalc.ui.tabs.materials_tab", "MaterialsTab"),
        ("electrocalc.ui.tabs.expenses_tab", "ExpensesTab"),
        ("electrocalc.ui.tabs.files_tab", "FilesTab"),
        ("electrocalc.ui.tabs.messages_tab", "MessagesTab"),
        ("electrocalc.ui.tabs.approvals_tab", "ApprovalsTab"),
        ("electrocalc.ui.tabs.education_tab", "EducationTab"),
        ("electrocalc.ui.tabs.dashboard_tab", "DashboardTab"),
        ("electrocalc.ui.tabs.users_tab", "UsersTab"),
        ("electrocalc.ui.tabs.company_tab", "CompanyTab"),
        ("electrocalc.ui.tabs.backup_tab", "BackupTab"),
        ("electrocalc.ui.tabs.audit_tab", "AuditTab"),
        ("electrocalc.ui.tabs.health_tab", "HealthTab"),
        ("electrocalc.ui.tabs.settings_tab", "SettingsTab"),
    ]
    errors = []
    for mod, cls in tabs:
        try:
            m = __import__(mod, fromlist=[cls])
            getattr(m, cls)
            print(f"  ✅ {mod}.{cls}")
        except Exception as e:
            print(f"  ❌ {mod}.{cls}  →  {e}")
            errors.append((mod, e))
    return errors


def test_database():
    section("۳) تست پایگاه داده")
    try:
        from electrocalc.data.database import get_connection, init_db
        init_db()
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = sorted(r[0] for r in cur.fetchall())
        print(f"  📋 جدول‌های موجود: {len(tables)}")
        for t in tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {t}")
                count = cur.fetchone()[0]
                print(f"     ✅ {t:25s}  ({count} رکورد)")
            except Exception as e:
                print(f"     ❌ {t:25s}  →  {e}")

        # انتظار
        expected = ["users", "projects", "project_members", "reports",
                    "timesheets", "materials", "expenses", "files",
                    "messages", "company", "active_sessions", "audit_log",
                    "app_settings", "notifications"]
        missing = [t for t in expected if t not in tables]
        if missing:
            print(f"\n  ⚠️ جدول‌های غایب: {missing}")
        else:
            print("\n  ✅ همه جدول‌ها موجود")

        conn.close()
    except Exception as e:
        print(f"  ❌ خطا: {e}")
        traceback.print_exc()


def test_settings():
    section("۴) تست تنظیمات")
    try:
        from electrocalc.core import settings as st
        keys = list(st.DEFAULTS.keys())
        data = st.get_all()
        print(f"  📋 {len(keys)} تنظیم موجود")
        for k in keys:
            v = data.get(k, "")
            print(f"     • {k:25s} = {v}")
    except Exception as e:
        print(f"  ❌ خطا: {e}")


def test_workers():
    section("۵) تست توابع حیاتی")
    try:
        from electrocalc.core import ohm, power, voltage_drop
        v = ohm.calc_voltage(2, 10)
        assert v == 20, "خطای قانون اهم"
        print(f"  ✅ قانون اهم: V = {v}")

        r = power.calc_power(220, 10, 0.9, False)
        print(f"  ✅ توان: P={r.p:.2f}W  S={r.s:.2f}VA  Q={r.q:.2f}VAR")

        vd = voltage_drop.calc_voltage_drop(220, 20, 50, 4, "copper", False, 1.0)
        print(f"  ✅ افت ولتاژ: {vd.drop_v:.2f}V ({vd.drop_percent:.2f}%)")
    except Exception as e:
        print(f"  ❌ خطا: {e}")


def test_file_structure():
    section("۶) ساختار پوشه‌ها")
    root = Path(__file__).resolve().parent
    important = [
        "electrocalc.db",
        "uploads",
        "logs",
        "backups",
        "assets",
        "electrocalc",
    ]
    for name in important:
        p = root / name
        if p.exists():
            if p.is_dir():
                print(f"  ✅ {name}/  (پوشه)")
            else:
                size = p.stat().st_size
                print(f"  ✅ {name}  ({size:,} بایت)")
        else:
            print(f"  ⚠️ {name}  →  موجود نیست")


def main():
    print("\n🔍 دیاگنوز پروژه THE Eminence")
    print("=" * 60)

    errs1 = test_imports()
    errs2 = test_tabs()
    test_database()
    test_settings()
    test_workers()
    test_file_structure()

    section("نتیجه نهایی")
    total_errors = len(errs1) + len(errs2)
    if total_errors == 0:
        print("  🎉 همه چیز سالمه!")
    else:
        print(f"  ⚠️ {total_errors} خطا پیدا شد:")
        for m, e in errs1 + errs2:
            print(f"     ❌ {m}: {e}")


if __name__ == "__main__":
    main()