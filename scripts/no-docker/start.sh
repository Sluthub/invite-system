#!/bin/bash
set -e

cd "$(dirname "$0")/../.."
source venv/bin/activate

export DATABASE_DIR="$PWD/data/database"
export LATEST_FILE="$PWD/latest"

cd dist/apps/wizarr-backend
gunicorn --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker --bind 127.0.0.1:5000 -m 007 run:app 2>&1
