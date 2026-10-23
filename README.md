# Campus Resolve

Django complaint and grievance system with email OTP verification, student/faculty roles, branch selection, complaint status tracking, and live dashboards.

## Run locally in VS Code (Windows PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open http://127.0.0.1:8000/. Create the first administrator with `python manage.py createsuperuser`; use `/admin/` to approve faculty accounts and assign complaint cases.

For local Gmail OTP delivery, copy `.env.example` to `.env`, set `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`, and add the sender's Google App Password to `EMAIL_HOST_PASSWORD`. Never commit `.env` or share the App Password.

## Deploy with Render

The repository includes `render.yaml` for a Render Blueprint. It creates a web service and PostgreSQL database in Singapore, configures production security, collects static files, applies migrations, and prompts for the Gmail App Password as a secret environment variable. The configuration uses paid compute plans. Review Render's current [compute plans](https://render.com/docs/compute-plans) and [pricing](https://render.com/pricing) before applying the Blueprint; deploying it creates billable resources.

1. Put this project in a GitHub repository and push the project files. Do not commit `.env`, `.venv`, or `db.sqlite3`.
2. In Render, create a new Blueprint from that repository and review the resources and plans before applying it.
3. When prompted for `EMAIL_HOST_PASSWORD`, enter the Gmail App Password privately in Render's environment-variable form. It is intentionally not stored in `render.yaml`.
4. When the first deploy is healthy, open the web service Shell and run `python manage.py createsuperuser` to create the production administrator.
5. Sign in to `/admin/`, approve faculty accounts, and assign incoming complaints.

The free Render web plan cannot send outbound SMTP on port 587, and a free Render Postgres database expires after 30 days. The included Blueprint uses paid plans so inbox OTP delivery and database persistence are available. See Render's [free instance limits](https://render.com/docs/free). No cloud service has been created by preparing these files.

## Deployment settings

- `DJANGO_DEBUG` is disabled in the Blueprint; production refuses the development fallback secret.
- `DATABASE_URL` configures PostgreSQL; local development continues to use SQLite.
- WhiteNoise serves collected static files.
- `/healthz/` checks both the web app and its database connection.
- HTTPS redirect, secure cookies, HSTS, allowed hosts, and trusted CSRF origins are set for production.
- Email uses the configured SMTP provider; secrets are provided through the host environment.
