#!/bin/sh
set -eu
cd "$(dirname "$0")/../.."
export DATABASE_DIR="${DATABASE_DIR:-$PWD/data/database}"
export HOST="${HOST:-127.0.0.1}"
export PORT="${PORT:-5000}"
export FLASK_ENV=production
FLASK_SKIP_SCHEDULER=true .venv/bin/flask db upgrade
exec .venv/bin/gunicorn --config gunicorn.conf.py run:app
