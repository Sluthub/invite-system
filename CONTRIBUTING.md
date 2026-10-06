# Contributing

Sluthub invitations uses the current Flask application at the repository root.
Install Python dependencies with `uv sync --locked --dev`. Install and build the
static frontend with `npm ci` and `npm run build` in `app/static`.

Use Python 3.13 and Node 24. Set `DATABASE_DIR` to a private development directory
before importing the application, then run `uv run flask db upgrade` and
`uv run flask run`. Keep live configuration and databases outside Git.

Run `uv run --locked --dev ruff check .` and
`uv run --locked --dev pytest -m 'not e2e'` for local checks. The Linux CI also
builds the static frontend and runs the Chromium browser tests. Install its
browser with `uv run --locked --dev playwright install chromium` when running
those tests locally.

Use conventional commit messages. Keep source refreshes, behavior changes and
deployment changes in reviewable checkpoints. Read
[the Sluthub migration guide](docs/sluthub-upgrade.md) before changing the
database or deployment layout.
