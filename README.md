# Construction Inventory & Supplier Management System

Production-grade offline-first Django 5 system using Clean Architecture and SOLID principles.

## Stack
- Django 5
- Django REST Framework
- MySQL
- Bootstrap 5
- HTML + JavaScript

## Run Modes
- Default settings module: `config.settings`
- Environment profiles via `.env`:
	- `DJANGO_ENV=offline` (SQLite, local/offline)
	- `DJANGO_ENV=online` (MySQL, secure cookies)
	- `DJANGO_ENV=test` (SQLite test database)

Business logic is isolated in the `src/application` and `src/domain` layers to support environment switching without use-case changes.

## Quick Start
1. Create a virtual environment.
2. Install dependencies from `requirements.txt`.
3. Configure `.env` values for MySQL and secrets.
4. Run migrations.
5. Start server with `python manage.py runserver`.

## Testing
- Unit + integration tests:
	`python manage.py test`

The test profile (`DJANGO_ENV=test`) uses SQLite for deterministic local execution and does not require MySQL connectivity.

## PythonAnywhere Deployment
1. Create a new PythonAnywhere web app using the manual Django setup.
2. Clone this GitHub repository in your PythonAnywhere console:

	`git clone https://github.com/hermankatende/iventory-sytem.git`

3. Create and activate a virtualenv, then install dependencies:

	`pip install -r requirements.txt`

4. Set environment variables in the PythonAnywhere web app or `.env` file:

	- `DJANGO_ENV=online`
	- `DEBUG=0`
	- `ALLOWED_HOSTS=<your-username>.pythonanywhere.com`
	- `DJANGO_SECRET_KEY=<secure-secret>`
	- MySQL settings if you use PythonAnywhere MySQL

5. Run migrations and collect static files:

	`python manage.py migrate`
	`python manage.py collectstatic --noinput`

6. Point the PythonAnywhere WSGI file at `config.wsgi.application`.
7. Add the static and media mappings in the PythonAnywhere Web tab.
8. Reload the web app and verify login, dashboard, payments, and reports.

## Architecture Documents
- `docs/architecture/01-complete-architecture.md`
- `docs/architecture/02-folder-structure.md`
- `docs/architecture/03-module-dependencies.md`
- `docs/architecture/04-design-patterns.md`
- `docs/architecture/05-security-design.md`
- `docs/architecture/06-database-design-strategy.md`
- `docs/architecture/07-production-readiness.md`
- `docs/architecture/08-offline-cloud-strategy.md`
