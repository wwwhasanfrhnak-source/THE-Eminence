# THE Eminence

**Professional Electrical Management System**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-pytest-informational)](https://pytest.org/)

THE Eminence is a local-first desktop workspace for organizing electrical service customers, projects, budgets, and operational reports.

## Features

- ⚡ Dark dashboard with business KPIs and performance charts
- 👥 Customer directory with create, edit, and delete workflows
- 🏗️ Project tracking, budgets, status, and schedule fields
- 🔐 bcrypt-backed accounts, role-based navigation, and session timeout
- 🧾 Activity logging for sign-in and record changes
- 📊 Customer report exports to Excel and PDF
- 💾 Local SQLite database with one-click backup
- 📅 Optional Jalali date formatting

## Screenshot

Screenshot placeholder: add a dashboard capture here.

## Install and run

Python 3.10 or later and the platform's Tk/Tcl package are required. On Linux, install Tkinter (for example, `sudo apt install python3-tk`) before proceeding.

### Windows

```powershell
py -3 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python main.py
```

### Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

### macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

The SQLite database is created at `data/db.sqlite` on first launch. Set `EMINENCE_DB_PATH`, `EMINENCE_LOG_LEVEL`, or `EMINENCE_SESSION_TIMEOUT` in the environment to configure the application.

## Default login

**Username:** `admin`  
**Password:** `admin123`

Change the initial administrator password before using the application with sensitive business data.

## Project structure

```text
THE_Eminence/
├── main.py
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── README.md
├── LICENSE
├── .gitignore
├── .env.example
├── .github/workflows/test.yml
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── theme.py
│   └── constants.py
├── core/
│   ├── __init__.py
│   ├── database.py
│   ├── schema.sql
│   ├── models.py
│   ├── repository.py
│   ├── exceptions.py
│   └── services/
│       ├── __init__.py
│       ├── auth_service.py
│       ├── customer_service.py
│       ├── project_service.py
│       ├── report_service.py
│       └── backup_service.py
├── auth/
│   ├── __init__.py
│   ├── session.py
│   ├── permissions.py
│   └── decorators.py
├── ui/
│   ├── __init__.py
│   ├── app.py
│   ├── router.py
│   ├── components/
│   │   ├── __init__.py
│   │   ├── pillow_utils.py
│   │   ├── modern_card.py
│   │   ├── sidebar.py
│   │   ├── kpi_card.py
│   │   ├── data_table.py
│   │   └── toast.py
│   └── views/
│       ├── __init__.py
│       ├── login_view.py
│       ├── dashboard_view.py
│       ├── customers_view.py
│       ├── projects_view.py
│       ├── reports_view.py
│       ├── users_view.py
│       └── settings_view.py
├── utils/
│   ├── __init__.py
│   ├── fonts.py
│   ├── security.py
│   ├── validators.py
│   ├── formatters.py
│   ├── date_helper.py
│   ├── pdf_export.py
│   ├── excel_export.py
│   └── logger.py
├── data/
│   ├── backups/
│   └── exports/
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_database.py
    ├── test_auth.py
    └── test_utils.py
```

## Development

```bash
python -m pip install -r requirements-dev.txt
python -m pytest tests/ -v
```

## Roadmap

- [ ] Transaction entry and project financial detail views
- [ ] Password change and account recovery workflows
- [ ] Configurable currencies and localization
- [ ] Automated backup scheduling and restore workflow
- [ ] Expanded dashboard filters and report templates

## License

MIT. See [LICENSE](LICENSE).
