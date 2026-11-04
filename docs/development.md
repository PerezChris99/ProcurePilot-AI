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

## Judges on macOS / Linux

From the repository root after installing Python 3.12+, Node.js 22.12+ (or 20.19+), npm and Git:

~~~bash
./start.sh
~~~

The Bash 3.2-compatible launcher detects the installed Python version, creates backend/.venv, installs Python/npm dependencies, copies env templates only if absent, defaults to SQLite for a **new** local demo, runs Alembic and a successful React production build before launching both local servers. Existing .env is **never modified**. Press Ctrl+C to stop. For a fresh PostgreSQL template use `./start.sh --postgres` and configure the local database before migrations. In a separate terminal run:

~~~bash
./verify.sh
~~~

Both scripts are executable in Git; if archive extraction strips execute permission use `bash ./start.sh` and `bash ./verify.sh`. They use the same real backend, React app and provider endpoints as Windows, with no mocked catalogue or payment responses.

## Current Windows VS Code routine

Open `D:\\NEW PROJECTS\\ProcurePilot-AI` in VS Code and run `.\\start.bat`. The launcher opens a dedicated VS Code window. If automatic folder-open tasks are blocked, press **Ctrl+Shift+P → Tasks: Run Task → ProcurePilot: Build then Start (VS Code Terminals)**. This runs the frontend build and migrations before opening the backend/frontend **integrated** terminals. Run `.\\verify.bat` independently from the repository root. Ensure PostgreSQL is already running; no launcher starts the database daemon.

## Responsive navigation and status

Desktop uses six distinct sidebar routes; phones/tablets get the same six links in an iPhone-safe-area bottom dock. Status is refreshed from the authenticated `/api/v1/integrations/status` endpoint, which checks DB/required schema and reports non-secret Gemini, Channel3 and PayPal credential flags. It is not a live provider ping and does not spend Gemini tokens. The user can refresh the panel manually and it polls while the workspace is active. Configure actual provider credentials in the root .env and restart the backend after changing them.

## Public site, authentication and provider landing tour

The browser now opens a **public** landing page at `/` for judges and guests. Sign in or register to enter the protected Overview at `/dashboard`. The remaining protected procurement paths (`/procurement`, `/discovery`, `/requests/:id`, `/approvals`, `/activity`, `/orders`) are unchanged. PayPal Sandbox returns to `/orders`; do not change that path in production without updating the PayPal return settings. The public website has honest About, How it works, Privacy, Terms, Security, Accessibility, Responsible use and Contact pages linked from the legal footer. The signed-in workspace and auth screens also link to legal pages.

The hero includes real Unsplash photography loaded from an HTTPS CDN. Judges need normal internet access to see remote photos; the content/navigation remain usable if media cannot load. Source and license: https://unsplash.com/license. Social proof is limited to named **integrated technologies**, not invented adoption statistics or endorsements.

Vercel SPA deep links: deploy with Root Directory `frontend`; `frontend/vercel.json` supplies the `/(.*)` → `/index.html` rewrite. Netlify: publish `frontend/dist`; the Vite build copies `frontend/public/_redirects` into the output. For both, use `npm run build:deploy` and a real public `VITE_API_BASE_URL`; a Vite development build with localhost must not be deployed unchanged.
