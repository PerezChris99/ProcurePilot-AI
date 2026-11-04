# Development

## Prerequisites

- Git
- Python 3.12+
- Node.js LTS and npm
- Visual Studio Code
- PostgreSQL for the configured local database (SQLite is used by isolated tests)

## Windows + VS Code quick start

1. Open the repository folder in VS Code.
2. Open the integrated terminal (**Terminal → New Terminal**).
3. Switch to the development branch and pull the latest changes:

   ```powershell
   git switch perez
   git pull origin perez
   ```

4. Run the repository bootstrap:

   ```powershell
   .\start.bat
   ```

The bootstrap creates `backend\.venv` when needed, installs `backend/requirements.txt`, creates local environment files from the examples only when they do not already exist, and installs frontend dependencies. It then opens the VS Code task picker. Select **ProcurePilot: Build then Start (VS Code Terminals)**.

The task sequence is deliberately gated:

1. Runs `npm run build` in `frontend/`.
2. Only after a successful build, starts FastAPI in a VS Code integrated terminal.
3. Starts the Vite development server in a second VS Code integrated terminal.

If the production build fails, the task sequence stops and neither application server is started. Build errors appear in the integrated terminal; fix them before retrying. The two server tasks remain running in VS Code and can be stopped with the terminal's stop/kill control.

You can also start the same sequence without the batch file using **Terminal → Run Task → ProcurePilot: Build then Start (VS Code Terminals)**. The task definitions live in `.vscode/tasks.json`.

Local URLs:

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API documentation: http://localhost:8000/docs

The launcher does not install or start PostgreSQL. The root `.env.example` configures PostgreSQL at `localhost:5432` with database name `procurepilot`; start PostgreSQL and create that database, or change `DATABASE_URL` in the root `.env` before starting the backend. Do not replace an existing `.env` file: the launcher intentionally preserves local credentials and configuration.

After configuring the database, apply migrations once from the repository root:

```powershell
Set-Location backend
.venv\Scripts\Activate.ps1
alembic upgrade head
```

The external Gemini, Channel3, and PayPal features require their corresponding backend credentials. Keep these secrets in the root/backend environment, never in frontend `VITE_` variables.

## Manual frontend setup

From `frontend/`:

```powershell
Copy-Item .env.example .env
npm install
npm run build
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

If PowerShell blocks virtual-environment activation, either use `backend\.venv\Scripts\python.exe -m pip ...` directly or adjust the current user's PowerShell execution policy according to your organization's policy. The batch bootstrap avoids PowerShell activation-policy issues.

Run backend tests from `backend/`:

```powershell
.venv/Scripts/Activate.ps1
pytest
pytest --cov=app --cov-report=term-missing
```

## Environment and secrets

The root `.env.example` is the backend environment template. The frontend `frontend/.env.example` contains only the public API base URL. Vite exposes variables prefixed with `VITE_` to browser code; never put API keys, database URLs, JWT secrets, or PayPal credentials in frontend variables.

Keep AI, Channel3, database, JWT, and PayPal secrets server-side. Never commit `.env` files or real credentials.
