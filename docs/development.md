# Development

## Prerequisites

- Node.js LTS and npm
- Python 3.12+
- PostgreSQL (or SQLite for isolated local tests)
- Git

## Frontend

From frontend: run npm install, npm run dev, npm test, npm run lint, and npm run build.

## Backend

From backend: create and activate a Python virtual environment, install requirements.txt, run pytest, and start the API with uvicorn app.main:app --reload.

Copy .env.example to an appropriate untracked local environment file and configure credentials. Never put secrets in frontend environment variables or commit them.
