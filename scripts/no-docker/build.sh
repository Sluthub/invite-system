#!/bin/bash
set -e

cd "$(dirname "$0")/../.."
source venv/bin/activate

rm -rf dist
npx nx build wizarr-frontend
npx nx build wizarr-backend
cd dist/apps/wizarr-backend
pip uninstall -y wizarr_backend
pip install wizarr_backend-*.whl
tar -xvzf wizarr_backend-*.tar.gz
mv wizarr_backend-*/wizarr_backend/* .
rm -rf wizarr_backend-*
