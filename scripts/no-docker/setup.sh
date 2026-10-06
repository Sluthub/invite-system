#!/bin/sh
set -eu
cd "$(dirname "$0")/../.."
command -v uv >/dev/null
command -v node >/dev/null
command -v npm >/dev/null
uv sync --locked --no-dev
