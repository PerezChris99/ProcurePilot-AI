#!/usr/bin/env bash
# ProcurePilot AI local judge launcher for macOS and Linux.
# First run chooses SQLite only if no .env exists; existing settings are sacred.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

MODE="${1:---demo}"
if [[ "$MODE" != "--demo" && "$MODE" != "--postgres" ]]; then
  printf 'Usage: ./start.sh [--demo|--postgres]\n' >&2
  exit 2
fi

printf '\n=== ProcurePilot AI | macOS / Linux ===\n'
command -v node >/dev/null || { echo '[ERROR] Install Node.js LTS 22.12+.' >&2; exit 1; }
command -v npm >/dev/null || { echo '[ERROR] npm is not installed.' >&2; exit 1; }
node "$ROOT/frontend/scripts/check-node-version.cjs"

PYTHON=''
for candidate in python3.14 python3.13 python3.12 python3; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" "$ROOT/backend/scripts/check_python_version.py" >/dev/null 2>&1; then
    PYTHON="$candidate"
    break
  fi
done
if [[ -z "$PYTHON" ]]; then
  echo '[ERROR] Python 3.12+ was not found. Install Python 3.12 or newer.' >&2
  exit 1
fi

echo '[1/6] Preparing the Python virtual environment'
if [[ ! -x "$ROOT/backend/.venv/bin/python" ]]; then
  "$PYTHON" -m venv "$ROOT/backend/.venv"
fi
VENV_PY="$ROOT/backend/.venv/bin/python"
"$VENV_PY" "$ROOT/backend/scripts/check_python_version.py"

echo '[2/6] Installing Python dependencies'
"$VENV_PY" -m pip install -r "$ROOT/backend/requirements.txt"

echo '[3/6] Preparing local environment'
if [[ ! -f "$ROOT/.env" ]]; then
  cp "$ROOT/.env.example" "$ROOT/.env"
  if [[ "$MODE" == "--demo" ]]; then
    "$VENV_PY" - "$ROOT/.env" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
template = "DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/procurepilot"
if template not in text:
    raise SystemExit("Cannot find the expected DATABASE_URL template")
path.write_text(text.replace(template, "DATABASE_URL=sqlite:///./procurepilot.db"), encoding="utf-8")
PY
    echo 'Created local .env using SQLite: PostgreSQL is NOT required for the demo.'
  else
    echo 'Created .env using PostgreSQL settings. Configure a running database before migration.'
  fi
else
  echo 'Existing .env preserved; DATABASE_URL and provider keys were not changed.'
fi
if [[ ! -f "$ROOT/frontend/.env" ]]; then
  cp "$ROOT/frontend/.env.example" "$ROOT/frontend/.env"
fi

echo '[4/6] Installing frontend dependencies'
if [[ -f "$ROOT/frontend/package-lock.json" ]]; then
  (cd "$ROOT/frontend" && npm ci --no-audit --no-fund)
else
  (cd "$ROOT/frontend" && npm install --no-audit --no-fund)
fi

echo '[5/6] Applying database migrations'
(cd "$ROOT/backend" && "$VENV_PY" -m alembic upgrade head)

echo '[6/6] Verifying the frontend production build'
(cd "$ROOT/frontend" && npm run build)

BACKEND_PID=''
FRONTEND_PID=''
cleanup() {
  trap - EXIT INT TERM
  if [[ -n "$FRONTEND_PID" ]]; then kill "$FRONTEND_PID" 2>/dev/null || true; fi
  if [[ -n "$BACKEND_PID" ]]; then kill "$BACKEND_PID" 2>/dev/null || true; fi
  if [[ -n "$FRONTEND_PID" ]]; then wait "$FRONTEND_PID" 2>/dev/null || true; fi
  if [[ -n "$BACKEND_PID" ]]; then wait "$BACKEND_PID" 2>/dev/null || true; fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

echo
echo 'Starting both servers. Keep this terminal open; press Ctrl+C to stop.'
echo 'UI:     http://127.0.0.1:5173'
echo 'API:    http://127.0.0.1:8000'
echo 'Docs:   http://127.0.0.1:8000/docs'
echo 'Health: http://127.0.0.1:8000/api/v1/ready'
echo

(cd "$ROOT/backend" && exec "$VENV_PY" -m uvicorn app.main:app --host 127.0.0.1 --port 8000) &
BACKEND_PID=$!
(cd "$ROOT/frontend" && exec node ./node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173 --strictPort) &
FRONTEND_PID=$!

# Bash 3.2 ships with macOS. Poll instead of using Bash 4.3-only wait -n.
while kill -0 "$BACKEND_PID" 2>/dev/null && kill -0 "$FRONTEND_PID" 2>/dev/null; do
  sleep 1
done
echo '[ERROR] A server stopped unexpectedly; shutting down the other server.' >&2
exit 1
