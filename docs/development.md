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

3. Run the bootstrap from the repository root:

   ```powershell
   .\\start.bat
   ```

The bootstrap prepares the backend virtual environment, installs Python and frontend dependencies, preserves existing local environment files, runs pending database migrations, and opens a dedicated VS Code window. The workspace task builds the frontend, verifies migrations, and starts FastAPI and Vite in separate integrated terminals. A missing database or failed migration stops startup rather than giving a misleading running UI. On first launch, trust the workspace and allow automatic tasks.

Local URLs:

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API documentation: http://localhost:8000/docs

## Database

The launcher cannot install or start PostgreSQL. Configure `DATABASE_URL` in the root `.env`, create the database, and make sure the PostgreSQL service is running. **Every `start.bat` run now executes `alembic upgrade head` automatically and stops before opening the app on migration failure.** The VS Code auto-start task repeats this idempotent migration check before the backend starts. For manual diagnosis, run from `backend/`:

```powershell
.\\.venv\\Scripts\\Activate.ps1
alembic upgrade head
alembic current
```

## External provider credentials

Follow [Provider setup and verification](provider-setup.md) to configure Google Gemini/ADK, Channel3, and PayPal Sandbox. The root `.env.example` is the backend template. The frontend `frontend/.env.example` contains only the public API base URL.

All provider secrets must remain in the root/backend environment. Never put them in frontend `VITE_*` variables or commit a real `.env` file.

After adding or changing provider credentials, restart the backend. The dashboard's **System status** panel reads the authenticated `GET /api/v1/integrations/status` endpoint. It shows safe configuration state and PostgreSQL connectivity; actual provider connectivity still requires running AI analysis, Channel3 discovery, and PayPal Sandbox checkout.

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

Run backend tests from `backend/`:

```powershell
.venv/Scripts/Activate.ps1
pytest
pytest --cov=app --cov-report=term-missing
```


## Single-command code checks

From the repository root on Windows, run `verify.bat` after `start.bat` has created the environments. It executes backend pytest, frontend ESLint, Vitest and the Vite production build in sequence. It stops on the first failure; it does **not** claim live Gemini/Channel3/PayPal calls, webhook delivery or deployed infrastructure readiness. The checked-in npm manifest presently does not have a tracked package lock, so dependency resolution can vary between installs. Record a validated lockfile before calling production builds reproducible.

## Judge-route notes and model budget

The authenticated /approvals route now has a dedicated page for pending submitted purchase orders. The /analyze endpoint automatically discovers from Channel3 once when no saved search exists; it uses saved results after that and returns cached responses for repeat clicks. The normal Google ADK analyst performs at most one model call and is limited by UTC database-backed user/global quotas in migration 0004_ai_budget.

New backend-only settings are AI_MAX_OUTPUT_TOKENS, AI_TIMEOUT_SECONDS, AI_DAILY_USER_RUNS, AI_DAILY_GLOBAL_RUNS and AI_EVIDENCE_CANDIDATES. Defaults are in the root .env.example. They do not belong in frontend/.env. See docs/agent.md and docs/testing.md for details.

Before each startup, stop existing VS Code backend/frontend terminal tasks or free ports 8000/5173; VS Code may require workspace trust and explicit permission before automatically running folder-open tasks. Database startup and third-party credential creation cannot be automated by the repository.

## Node.js / local browser safety

The launcher now checks Node.js **20.19+** or **22.12+** before dependency installation because Vite 7 requires these ranges. Node 18 and 21 are unsupported. The development server defaults to loopback (`127.0.0.1`) rather than listening on the public network. Local bootstrap still works with `APP_ENV=development`; production mode requires an HTTPS frontend origin, a strong JWT secret, and a PostgreSQL URL using the installed psycopg driver.

## Public build verification

Run npm run test:deploy-config in frontend/ to test endpoint validation with Node's built-in test runner. Configure VITE_API_BASE_URL with a real HTTPS backend URL ending in /api/v1 or the same-origin path /api/v1 behind a reverse proxy, then run npm run build:deploy. The default local npm run build remains unchanged. Configure your deployment service to use the strict command and do not place provider credentials inside VITE-prefixed values.

## Windows batch parser resilience

The launcher runs small, checked-in Node and Python preflight scripts instead of embedding nested JavaScript/Python expressions within Windows CMD conditional blocks. This avoids CMD interpreting parentheses or shell control symbols before displaying the first setup stage. If an older startup script reports an unexpected token, pull the latest perez branch before retrying. The frontend Node version tests run through verify.bat; the Python preflight requires only the standard library.

## Local CORS and expired sessions

The React/Vite server may be visited as either `http://localhost:5173` or `http://127.0.0.1:5173`, which are different browser origins. In development/test environments, FastAPI now allows the configured loopback origin **and** its equivalent loopback hostname at the same scheme/port. Staging/production continue allowing only the exact HTTPS `FRONTEND_URL`, with no wildcard or extra origins. If a browser preflight for `/api/v1/auth/login` returns HTTP 400, verify the address bar origin against the configured frontend URL and restart the backend after changing `.env`. An `/auth/me` HTTP 401 normally indicates that an existing short-lived bearer token has expired or been rejected; the frontend clears it and offers sign-in, and a fresh successful login obtains a new token. CORS restrictions should not be relaxed to solve an invalid token.
