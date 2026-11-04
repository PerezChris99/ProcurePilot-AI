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

The bootstrap prepares the backend virtual environment, installs Python and frontend dependencies, preserves existing local environment files, and opens a dedicated VS Code window. The workspace task builds the frontend before starting FastAPI and Vite in separate integrated terminals. On first launch, trust the workspace and allow automatic tasks.

Local URLs:

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API documentation: http://localhost:8000/docs

## Database

The launcher does not install or start PostgreSQL. Configure `DATABASE_URL` in the root `.env`, create the database, then run migrations from `backend/`:

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

