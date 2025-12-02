# Meal Tracker

## Overview
- Django 5-based meal tracking app for shared kitchens/hostels.
- Tracks members, daily meal attendance, daily price per meal, payments, and weekly balances.
- Default week runs Saturday–Friday; dashboard summarizes the current week.
- Desktop launcher (`desktop_main.py`) can serve the app via Waitress and optionally open a PyWebView window.

## Project Layout
- `manage.py` – Django management entrypoint.
- `meal_tracker/` – project settings/URL routing/WSGI; static root configured at `staticfiles/`.
- `tracker/` – main app with models (`Member`, `MealPrice`, `MealRecord`, `Payment`), views, and templates.
- `desktop_main.py` – starts Waitress on `127.0.0.1:8000` and opens the UI (falls back to the browser if PyWebView is unavailable).
- `build_app.spec` – PyInstaller configuration used to produce a Windows executable.
- `db.sqlite3` – SQLite database (kept as requested).

## Setup & Running
1) Install dependencies (inside a virtualenv recommended):
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```
2) Apply migrations if you start with a fresh database:
```bash
python manage.py migrate
```
3) Run the web app for development:
```bash
python manage.py runserver
```
4) Desktop wrapper (serves via Waitress and opens a window/tab):
```bash
python desktop_main.py
```
5) Deploying/collecting static assets (regenerate `staticfiles/`):
```bash
python manage.py collectstatic --noinput
```
6) Build a Windows executable (recreates `dist/`):
```bash
pyinstaller build_app.spec
```

## Core Workflow
- **Manage members** (`/manage-members/`): add new members, edit names, toggle active/inactive.
- **Set meal price** (`/manage-price/`): enter the per-meal price by date (one price per day).
- **Mark daily meals** (`/daily-meals/`): toggle attendance for each member/day; navigate weeks via the `week` query parameter.
- **Record payments** (`/manage-payments/`): log payments with amount, date, and optional note.
- **Review dashboard** (`/`): weekly summary (Saturday–Friday) per active member showing meals, total bill (based on that week's prices), paid amount, and unpaid balance.

## Data Model Snapshot
- `Member`: name, `serial_number`, `is_active`; helpers for week start, weekly meals, totals, and balances.
- `MealPrice`: `date`, `price_per_meal`; most recent entries appear first.
- `MealRecord`: one per member/day (`unique_together`), tracks `ate_meal` and `meal_count`.
- `Payment`: payment records per member with amount, date, and optional note.

## Maintenance Notes
- Removed generated artifacts (`build/`, `dist/`, `staticfiles/`, `__pycache__`) to keep the repo lean; regenerate via the commands above when needed.
- Static files are served via WhiteNoise; ensure you run `collectstatic` before packaging or serving in production.

## Docker Deployment
- Build and run with Postgres via Compose:
```bash
docker-compose up --build
```
- Copy `.env.sample` to `.env` and set values: `DJANGO_SECRET_KEY` (required), `DJANGO_DEBUG` (`False` for production), `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, database settings (`DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`), and Postgres container vars (`POSTGRES_*`).
- Entrypoint (`/entrypoint.sh`) runs `migrate`, `collectstatic`, then starts Waitress on `${PORT:-8000}` with `${WEB_CONCURRENCY:-4}` threads.
