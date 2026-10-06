"""Convert the old Nx/Peewee database into a fresh current Wizarr database.

Run under the current Flask application after its Alembic migrations. The source
is opened read-only; no media-server, request-service or notification calls occur.
Keep the original database and sessions in the protected recovery directory.
"""

import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.extensions import db
from app.models import (
    AdminAccount,
    Connection,
    Identity,
    Invitation,
    Library,
    MediaServer,
    Settings,
    User,
    WizardBundle,
    WizardBundleStep,
    WizardStep,
    invitation_servers,
    invitation_users,
)
from app.services.wizard_presets import create_step_from_preset


def _date(value, source_timezone="UTC"):
    if not value:
        return None
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=ZoneInfo(source_timezone))
    return parsed.astimezone(UTC).replace(tzinfo=None)


def _read_source(path: Path) -> dict[str, list[dict]]:
    with closing(
        sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    ) as con:
        con.row_factory = sqlite3.Row
        tables = {
            r[0]
            for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        required = {
            "accounts": "SELECT * FROM accounts",
            "invitations": "SELECT * FROM invitations",
            "users": "SELECT * FROM users",
            "settings": "SELECT * FROM settings",
            "onboarding": "SELECT * FROM onboarding",
            "requests": "SELECT * FROM requests",
            "libraries": "SELECT * FROM libraries",
        }
        if not required.keys() <= tables:
            raise ValueError("Source is not the supported Nx/Peewee database")
        unsupported = {
            "mfa": "SELECT count(*) FROM mfa",
            "apikeys": "SELECT count(*) FROM apikeys",
            "oauthclients": "SELECT count(*) FROM oauthclients",
            "discord": "SELECT count(*) FROM discord",
            "webhooks": "SELECT count(*) FROM webhooks",
            "memberships": "SELECT count(*) FROM memberships",
            "licenses": "SELECT count(*) FROM licenses",
            "notifications": "SELECT count(*) FROM notifications",
        }
        for table in unsupported.keys() & tables:
            if con.execute(unsupported[table]).fetchone()[0]:
                raise ValueError(
                    f"Nonempty legacy {table} requires a separate migration"
                )
        data = {
            table: [dict(r) for r in con.execute(required[table])] for table in required
        }
        data["sessions"] = (
            [dict(r) for r in con.execute('SELECT id FROM "sessions"')]
            if "sessions" in tables
            else []
        )
        return data


def migrate_legacy(source: Path, legacy_used_timezone="UTC") -> dict:
    """Import a validated source once, committing all target changes together."""
    data = _read_source(source)
    ZoneInfo(legacy_used_timezone)
    if not data["accounts"]:
        raise ValueError("Legacy administrator account is missing")
    if any(
        model.query.count()
        for model in (
            AdminAccount,
            User,
            Invitation,
            MediaServer,
            Connection,
            WizardBundle,
            Library,
            Identity,
        )
    ):
        raise ValueError("Destination must be a fresh migrated database")
    settings = {r["key"]: r["value"] for r in data["settings"]}
    server_type = settings.get("server_type")
    if server_type not in {"jellyfin", "emby", "plex"}:
        raise ValueError("Unsupported legacy media-server type")
    if not settings.get("server_url") or not settings.get("server_api_key"):
        raise ValueError("Legacy media-server configuration is incomplete")
    if any(r.get("duration") for r in data["invitations"]):
        raise ValueError("Nonempty legacy membership duration requires review")
    if any(not 6 <= len(r["code"]) <= 10 for r in data["invitations"]):
        raise ValueError("Legacy invitation length requires review")
    if any(r["role"] != "admin" for r in data["accounts"]):
        raise ValueError("Legacy non-administrator roles require review")
    for account in data["accounts"]:
        if not account["password"].startswith(("scrypt:", "pbkdf2:")):
            raise ValueError("Legacy administrator password format requires review")
    supported_requests = {
        "jellyseerr": "seerr",
        "seerr": "seerr",
        "overseerr": "overseerr",
        "ombi": "ombi",
    }
    if any(r["service"] not in supported_requests for r in data["requests"]):
        raise ValueError("Unsupported legacy request-service type")
    if any(r.get("template") not in {None, 1, 2, 3} for r in data["onboarding"]):
        raise ValueError("Unsupported legacy onboarding template")
    now = datetime.now(UTC).replace(tzinfo=None)
    report = {
        "users": 0,
        "invitations": 0,
        "administrators": 0,
        "connections": 0,
        "onboarding_steps": 0,
        "user_invite_links": 0,
        "stale_user_references": 0,
        "legacy_login_sessions_invalidated": len(data["sessions"]),
    }
    try:
        server = MediaServer(
            name=settings.get("server_name") or "Sluthub",
            server_type=server_type,
            url=settings["server_url"],
            api_key=settings["server_api_key"],
            external_url=settings.get("server_url_override") or settings["server_url"],
            verified=str(settings.get("server_verified", "")).lower()
            in {"true", "1", "yes"},
        )
        db.session.add(server)
        db.session.flush()
        for account in data["accounts"]:
            db.session.add(
                AdminAccount(
                    id=account["id"],
                    username=account["username"],
                    password_hash=account["password"],
                    created_at=_date(account.get("created")) or now,
                    auth_source="local",
                )
            )
        public_settings = {
            "server_name": server.name,
            "admin_username": data["accounts"][0]["username"],
            "discord_id": settings.get("server_discord_id") or "",
        }
        for request in data["requests"]:
            db.session.add(
                Connection(
                    name=request["name"],
                    connection_type=supported_requests[request["service"]],
                    url=request["url"],
                    api_key=request["api_key"],
                    media_server_id=server.id,
                    created_at=_date(request.get("created")) or now,
                    updated_at=now,
                )
            )
            public_settings.setdefault("overseerr_url", request["url"])
        for key, value in public_settings.items():
            row = Settings.query.filter_by(key=key).first()
            if row:
                row.value = value
            else:
                db.session.add(Settings(key=key, value=value))
        users = {}
        for row in data["users"]:
            identity = Identity(
                primary_username=row["username"],
                primary_email=row.get("email"),
                created_at=_date(row.get("created")) or now,
            )
            db.session.add(identity)
            user = User(
                id=row["id"],
                token=row["token"],
                username=row["username"],
                email=row.get("email"),
                code=row.get("code") or "",
                expires=_date(row.get("expires")),
                server=server,
                identity=identity,
                created_at=_date(row.get("created")) or now,
            )
            db.session.add(user)
            users[user.id] = user
        libraries = {}
        for row in data["libraries"]:
            libraries[str(row["id"])] = Library(
                external_id=str(row["id"]),
                name=row["name"],
                enabled=True,
                server=server,
            )
            db.session.add(libraries[str(row["id"])])
        bundle = WizardBundle(
            name="Sluthub onboarding",
            description="Preserved from the legacy Sluthub invitation service",
        )
        db.session.add(bundle)
        db.session.flush()
        # Only the fresh target's built-in post-invite steps are replaced.
        WizardStep.query.filter_by(
            server_type=server_type, category="post_invite"
        ).delete()
        for row in sorted(data["onboarding"], key=lambda r: r["order"]):
            if not row["enabled"]:
                continue
            template = row.get("template")
            if template == 1:
                markdown = create_step_from_preset(
                    "discord_community", discord_id=public_settings["discord_id"]
                )
                title = "Sluthub community"
            elif template == 2:
                markdown = create_step_from_preset(
                    "overseerr_requests",
                    overseerr_url=public_settings.get("overseerr_url", ""),
                )
                title = "Request new titles"
            else:
                markdown = row.get("value") or "## Welcome to Sluthub"
                title = "Sluthub apps" if template == 3 else "Welcome to Sluthub"
                if template == 3:
                    markdown += (
                        '\n\n{{ widget:button url="external_url" text="Open Sluthub" }}'
                    )
            position = report["onboarding_steps"]
            step = WizardStep(
                server_type=server_type,
                category="post_invite",
                position=position,
                title=title,
                markdown=markdown,
                requires=[],
                created_at=now,
                updated_at=now,
            )
            db.session.add(step)
            db.session.flush()
            db.session.add(
                WizardBundleStep(
                    bundle_id=bundle.id, step_id=step.id, position=position
                )
            )
            report["onboarding_steps"] += 1
        db.session.flush()
        for row in data["invitations"]:
            invite = Invitation(
                id=row["id"],
                code=row["code"],
                used=bool(row["used"]),
                used_at=_date(row.get("used_at"), legacy_used_timezone),
                created=_date(row.get("created")) or now,
                expires=_date(row.get("expires")),
                unlimited=bool(row.get("unlimited")),
                duration=None,
                specific_libraries=row.get("specific_libraries"),
                plex_allow_sync=bool(row.get("plex_allow_sync")),
                allow_downloads=bool(row.get("allow_download")),
                allow_live_tv=bool(row.get("live_tv")),
                allow_mobile_uploads=False,
                max_active_sessions=row.get("sessions"),
                server=server,
                wizard_bundle=bundle,
            )
            for external_id in filter(
                None, (row.get("specific_libraries") or "").split(",")
            ):
                if external_id not in libraries:
                    libraries[external_id] = Library(
                        external_id=external_id,
                        name="Legacy restricted library",
                        enabled=True,
                        server=server,
                    )
                    db.session.add(libraries[external_id])
                invite.libraries.append(libraries[external_id])
            invite.servers.append(server)
            db.session.add(invite)
            db.session.flush()
            associated = {u.id for u in users.values() if u.code == invite.code}
            for reference in filter(None, (row.get("used_by") or "").split(",")):
                if reference.isdigit() and int(reference) in users:
                    associated.add(int(reference))
                else:
                    report["stale_user_references"] += 1
            for user_id in sorted(associated):
                db.session.execute(
                    invitation_users.insert().values(
                        invite_id=invite.id,
                        user_id=user_id,
                        server_id=server.id,
                        used_at=invite.used_at or now,
                    )
                )
                report["user_invite_links"] += 1
            if associated:
                invite.used_by = users[min(associated)]
            db.session.execute(
                invitation_servers.update()
                .where(invitation_servers.c.invite_id == invite.id)
                .values(used=invite.used, used_at=invite.used_at)
            )
        db.session.flush()
        report.update(
            users=len(data["users"]),
            invitations=len(data["invitations"]),
            administrators=len(data["accounts"]),
            connections=len(data["requests"]),
        )
        if (
            User.query.count() != report["users"]
            or Invitation.query.count() != report["invitations"]
        ):
            raise ValueError("Converted database counts do not match the source")
        if db.session.execute(db.text("PRAGMA foreign_key_check")).fetchall():
            raise ValueError("Converted database has invalid relationships")
        db.session.commit()
        return report
    except Exception:
        db.session.rollback()
        raise
