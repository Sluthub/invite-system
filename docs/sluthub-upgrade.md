# Sluthub invitations

This fork uses Wizarr 2026.9.1 with Sluthub branding, the current Flask interface,
and the existing invitations, onboarding and request-service integration.
The old Nx application remains available in Git history.

Use Python 3.13 and a supported Node 24 runtime. Install Python dependencies with
`uv sync --locked --no-dev`, then run `npm ci` and `npm run build` in `app/static`.
Compile the bundled translations with
`uv run --locked --no-dev pybabel compile -d app/translations`.

The static dependency graph overrides Typography's pinned selector parser to
7.1.6 for its security fix. Parser 7 makes mutation during iteration safe; the
`astSync`, node removal and selector-construction APIs used by Typography remain
compatible. Verify the generated CSS against the previous locked graph and run
the static build before changing this override.

`scripts/no-docker/start.sh` starts the current application on loopback port 5000.
Set `DATABASE_DIR` to the intended private data directory before importing the
application. Configuration, sessions and the SQLite database use that directory.

## Migrating the old live application

The legacy Peewee tables cannot be upgraded directly with Alembic. First create a
fresh private destination, run its Alembic migrations, and call
`app.scripts.migrate_sluthub_legacy.migrate_legacy` inside its Flask application
context with a read-only copy of the legacy database. For the Sluthub deployment,
pass `legacy_used_timezone="Europe/Berlin"`: the old application recorded invite
usage in local time, while creation and expiry timestamps were UTC.

The converter preserves media user IDs, usernames, emails, expiry dates,
administrator password hashes, invitation codes and usage associations, library
restrictions, download/live-TV/session limits, request connections and enabled
onboarding pages. Its Seerr integration imports only the newly invited media
user. Existing administrator login sessions require a fresh login after migration.
Existing `/i/<code>` links redirect to the current `/j/<code>` invitation flow.

The converter refuses an existing destination or unmapped legacy data. Test the
actual database conversion and the application with outbound networking disabled
before promoting it. Keep the old source, private database, configuration and
service definition available for rollback; do not replace a dirty live checkout.
