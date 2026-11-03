# Development

## Prerequisites

- Node.js LTS and npm
- Python 3.12+
- PostgreSQL (SQLite is used for isolated tests)
- Git

## Frontend

From the frontend directory, copy .env.example to .env, install dependencies with npm install, and run npm run dev. Before committing, run npm test, npm run lint, and npm run build.

## Backend

From the backend directory, create and activate a Python virtual environment, install dependencies with pip install -r requirements.txt, and copy ../.env.example to .env (or configure environment variables directly). Run database migrations with alembic upgrade head, execute tests with pytest, and start the API with uvicorn app.main:app --reload.

Never put credentials in VITE_ variables: Vite exposes those values to browser code. The frontend .env file must contain only the public API base URL. Keep AI, Channel3, database, JWT, and PayPal secrets in the backend environment.
