# CampusPass

Web app for **supervised student exit and entry** at Ugandan schools (Primary P1–P7, Secondary S1–S6, optional streams).

## Features

- Multi-school registration with **superadmin** approval
- Roles: admin, nurse, teacher, guard, parent
- Movement requests (nurse, teacher, **parent**) → admin approve/reject
- Learner roster with present/absent status, Excel import/export, **edit/delete**
- **RFID** gate: hardware API (`POST /rfid_scan`) + guard **web scanner** + manual lookup
- In-app notifications for teachers, parents, and admins; optional **email** via SMTP
- Passwords stored with **Werkzeug hashing** (legacy plain passwords upgraded on login)

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env          # optional: set SECRET_KEY, mail, RFID_API_KEY
python app.py
```

Open http://127.0.0.1:5000

**Default superadmin:** `superadmin@system.com` / `admin123` (change after first login in production)

## Configuration (.env)

| Variable | Purpose |
|----------|---------|
| `SECRET_KEY` | Flask session signing (required in production) |
| `DATABASE_URL` | SQLAlchemy URI (default: `instance/school.db`) |
| `RFID_API_KEY` | If set, hardware must send `X-RFID-API-Key` header |
| `MAIL_*` | Optional SMTP for email alerts |

## Production

```bash
pip install gunicorn
gunicorn -w 2 -b 0.0.0.0:8000 wsgi:app
```

Or use the included `Procfile` on platforms like Render/Heroku.

## Tests

```bash
pytest
```

## RFID hardware

```http
POST /rfid_scan
Content-Type: application/json
X-RFID-API-Key: your-key-if-configured

{"rfid": "TAG-123", "guard_id": 5}
```

Guards can also use **RFID scanner** in the web UI (logged in as guard).

## Project layout

- `app.py` — routes and application logic
- `models.py` — SQLAlchemy models
- `auth_utils.py` — password hashing
- `notify.py` — notifications and optional email
- `curriculum_ug.py` — class codes
- `excel_import.py` — learner spreadsheet import
- `templates/` — Jinja2 HTML
- `tests/` — pytest suite
