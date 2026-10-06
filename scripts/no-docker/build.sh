#!/bin/sh
set -eu
cd "$(dirname "$0")/../.."
./scripts/no-docker/setup.sh
(cd app/static && npm ci && npm run build)
.venv/bin/pybabel compile -d app/translations
