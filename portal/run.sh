#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt

export PORTAL_HOST="${PORTAL_HOST:-127.0.0.1}"
export PORTAL_PORT="${PORTAL_PORT:-8787}"

echo "Agentic portal → http://${PORTAL_HOST}:${PORTAL_PORT}"
exec python app.py
