#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
VENV_PY="$ROOT/backend/.venv/bin/python"
if [[ ! -x "$VENV_PY" || ! -d "$ROOT/frontend/node_modules" ]]; then
  echo '[ERROR] Local dependencies are missing. Run ./start.sh first.' >&2
  exit 1
fi

printf '\n=== ProcurePilot AI | Local verification ===\n'
echo '[1/5] Bash and Python syntax and source'
bash -n "$ROOT/start.sh" "$ROOT/verify.sh"
(cd "$ROOT/backend" && "$VENV_PY" -m compileall -q app tests)
echo '[2/5] Backend tests'
(cd "$ROOT/backend" && "$VENV_PY" -m pytest -q)
echo '[3/5] Frontend ESLint'
(cd "$ROOT/frontend" && npm run lint)
echo '[4/5] Frontend Vitest and Node regression tests'
(cd "$ROOT/frontend" && npm test && npm run test:deploy-config)
echo '[5/5] Frontend production build'
(cd "$ROOT/frontend" && npm run build)
echo '[PASSED] All local source, test and build gates completed.'
echo 'Live Gemini, Channel3, PayPal Sandbox, signed webhooks and deployed infrastructure remain separate acceptance gates.'
