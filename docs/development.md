# Development

## Prerequisites

- Git
- Python 3.12+
- Node.js LTS and npm
- PostgreSQL for the configured local database (SQLite is used by isolated tests)

## Windows quick start

From the repository root, run:

```bat
start.bat
```

The launcher creates `backend\\.venv` when needed, installs `backend/requirements.txt`, creates local `.env` files from the examples if they do not exist, installs frontend packages, and opens separate terminal windows for the FastAPI backend and Vite frontend.

Local URLs:

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API documentation: http://localhost:8000/docs

The launcher does not install or start PostgreSQL. The root `.env.example` configures PostgreSQL at `localhost:5432` with database name `procurepilot`; start PostgreSQL and create that database, or change `DATABASE_URL` in the root `.env` before starting the backend. Do not replace an existing `.env` file: the launcher intentionally preserves local credentials and configuration.

After configuring the database, apply migrations once from the repository root:

```bat
cd backend
.venv\\Scripts\\activate
alembic upgrade head
```

The external Gemini, Channel3, and PayPal features require their corresponding backend credentials. Keep these secrets in the root/backend environment, never in frontend `VITE_` variables.

## Manual frontend setup

From `frontend/`:

```powershell
Copy-Item .env.example .env
npm install
npm run dev
```

Before committing, run:

```powershell
npm test
npm run lint
npm run build
```

## Manual backend setup

From the repository root:

```powershell
py -3.12 -m venv backend/.venv
backend/.venv/Scripts/Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
Copy-Item .env.example .env
Set-Location backend
alembic upgrade head
python -m uvicorn app.main:app --reload
```

If PowerShell blocks virtual-environment activation, either use `backend\\.venv\\Scripts\\python.exe -m pip ...` directly or adjust the current user's PowerShell execution policy according to your organization's policy. The batch launcher avoids PowerShell activation-policy issues.

Run backend tests from `backend/`:

```powershell
.venv/Scripts/Activate.ps1
pytest
pytest --cov=app --cov-report=term-missing
```

## Environment and secrets

The root `.env.example` is the backend environment template. The frontend `frontend/.env.example` contains only the public API base URL. Vite exposes variables prefixed with `VITE_` to browser code; never put API keys, database URLs, JWT secrets, or PayPal credentials in frontend variables.

Keep AI, Channel3, database, JWT, and PayPal secrets server-side. Never commit `.env` files or real credentials.
