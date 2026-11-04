# Development

## Prerequisites

- Git
- Python 3.12+
- Node.js LTS and npm
- Visual Studio Code
- PostgreSQL for the configured local database (SQLite is used by isolated tests)

## Windows + VS Code quick start

1. Clone the repository and open it in VS Code:

   ```powershell
   Set-Location "D:\\NEW PROJECTS"
   git clone https://github.com/PerezChris99/ProcurePilot-AI.git
   Set-Location ".\\ProcurePilot-AI"
   code .
   ```

2. Switch to the development branch and pull the latest changes:

   ```powershell
   git switch perez
   git pull origin perez
   ```

3. Run the bootstrap from the repository root (PowerShell or a terminal):

   ```powershell
   .\\start.bat
   ```

The bootstrap creates `backend\\.venv` when needed, installs `backend/requirements.txt`, creates local environment files from examples only when they do not already exist, and installs frontend dependencies. It attempts `npm ci` when a lockfile exists; if npm rejects a stale or inconsistent lockfile, it falls back to `npm install`. If dependency installation fails, the bootstrap stops and displays the underlying error.

After installation, the script opens a **dedicated VS Code window** for the repository. The compound task in `.vscode/tasks.json` is configured to run automatically when that workspace opens:

1. Runs `npm run build` in `frontend/`.
2. Only after a successful build, starts FastAPI in one VS Code integrated terminal.
3. Waits for FastAPI readiness, then starts Vite in a second VS Code integrated terminal.

**First launch requirements:** VS Code may ask whether you trust the folder and whether to allow automatic tasks. Choose **Trust** and **Allow Automatic Tasks**. If the workspace is in Restricted Mode or automatic tasks are denied, VS Code will not launch the terminals automatically. The batch file does not use an undocumented VS Code CLI command; it opens the workspace and lets VS Code's supported folder-open task mechanism start the processes.

The build is a gate: if it fails, the backend and frontend servers are not started. Read the build error in the VS Code terminal, fix it, then run **Terminal → Run Task → ProcurePilot: Build then Start (VS Code Terminals)** or press **Ctrl+Shift+B** (the compound task is the default build task).

Local URLs:

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API documentation: http://localhost:8000/docs

The launcher does not install or start PostgreSQL. The root `.env.example` configures PostgreSQL at `localhost:5432` with database name `procurepilot`; start PostgreSQL and create that database, or change `DATABASE_URL` in the root `.env` before starting the backend. The launcher preserves existing local configuration.

After configuring the database, apply migrations once from the repository root:

```powershell
Set-Location backend
.venv\\Scripts\\Activate.ps1
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

If PowerShell blocks virtual-environment activation, either use `backend\\.venv\\Scripts\\python.exe -m pip ...` directly or adjust the current user's PowerShell execution policy according to your organization's policy. The batch bootstrap avoids PowerShell activation-policy issues.

Run backend tests from `backend/`:

```powershell
.venv/Scripts/Activate.ps1
pytest
pytest --cov=app --cov-report=term-missing
```

## Environment and secrets

The root `.env.example` is the backend environment template. The frontend `frontend/.env.example` contains only the public API base URL. Vite exposes variables prefixed with `VITE_` to browser code; never put API keys, database URLs, JWT secrets, or PayPal credentials in frontend variables.

Keep AI, Channel3, database, JWT, and PayPal secrets server-side. Never commit `.env` files or real credentials.
