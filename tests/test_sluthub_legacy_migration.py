import hashlib
import sqlite3
from contextlib import closing
from datetime import UTC, datetime

import pytest
from werkzeug.security import generate_password_hash

from app.models import (
    AdminAccount,
    Connection,
    Invitation,
    MediaServer,
    User,
    WizardStep,
)
from app.scripts.migrate_sluthub_legacy import migrate_legacy


@pytest.fixture
def legacy_database(tmp_path):
    path = tmp_path / "legacy.db"
    with closing(sqlite3.connect(path)) as con:
        con.executescript("""
            CREATE TABLE accounts (id INTEGER, username TEXT, password TEXT, role TEXT, created TEXT);
            CREATE TABLE settings (key TEXT, value TEXT);
            CREATE TABLE users (id INTEGER, token TEXT, username TEXT, email TEXT, code TEXT, expires TEXT, created TEXT);
            CREATE TABLE invitations (id INTEGER, code TEXT, used INTEGER, used_at TEXT, used_by TEXT, created TEXT, expires TEXT, unlimited INTEGER, duration TEXT, specific_libraries TEXT, plex_allow_sync INTEGER, sessions INTEGER, live_tv INTEGER, hide_user INTEGER, allow_download INTEGER);
            CREATE TABLE onboarding (value TEXT, "order" INTEGER, enabled INTEGER, template INTEGER);
            CREATE TABLE requests (name TEXT, service TEXT, url TEXT, api_key TEXT, created TEXT);
            CREATE TABLE libraries (id TEXT, name TEXT);
            CREATE TABLE sessions (id INTEGER);
            CREATE TABLE mfa (id INTEGER);
            INSERT INTO settings VALUES ('server_type','jellyfin'),('server_name','Sluthub'),('server_url','http://127.0.0.1:8096'),('server_url_override','https://sluthub.example.invalid'),('server_api_key','fixture-media-key'),('server_verified','True'),('server_discord_id','12345');
            INSERT INTO users VALUES (10,'media-id-10','alice','alice@example.invalid','ABCDEF','2027-01-01T00:00:00+00:00','2026-01-01 00:00:00'),(11,'media-id-11','bob',NULL,'ABCDEF',NULL,'2026-01-02 00:00:00');
            INSERT INTO invitations VALUES (5,'ABCDEF',1,'2026-01-02 00:00:00','10,11','2026-01-01 00:00:00',NULL,1,NULL,'restricted-library',0,2,1,1,1),(6,'GHIJKL',0,NULL,NULL,'2026-01-03 00:00:00',NULL,0,NULL,NULL,0,0,0,1,0);
            INSERT INTO requests VALUES ('Sluthub requests','jellyseerr','https://requests.example.invalid','fixture-request-key','2026-01-01 00:00:00');
            INSERT INTO onboarding VALUES ('## Welcome to Sluthub',0,1,NULL),('Download instructions',1,1,3),(NULL,2,1,1),(NULL,3,1,2);
            INSERT INTO sessions VALUES (1),(2);
        """)
        con.execute(
            "INSERT INTO accounts VALUES (1,?,?,?,?)",
            (
                "administrator",
                generate_password_hash("fixture-password"),
                "admin",
                "2026-01-01 00:00:00",
            ),
        )
        con.commit()
    return path


def test_preserves_accounts_invites_permissions_and_onboarding(
    session, legacy_database
):
    before = hashlib.sha256(legacy_database.read_bytes()).digest()
    report = migrate_legacy(legacy_database)
    assert hashlib.sha256(legacy_database.read_bytes()).digest() == before
    assert report["users"] == 2
    assert report["invitations"] == 2
    assert report["administrators"] == 1
    assert report["onboarding_steps"] == 4
    assert report["user_invite_links"] == 2
    assert report["legacy_login_sessions_invalidated"] == 2
    assert AdminAccount.query.one().check_password("fixture-password")
    assert User.query.filter_by(id=10).one().expires.replace(tzinfo=UTC) == datetime(
        2027, 1, 1, tzinfo=UTC
    )
    assert User.query.filter_by(id=11).one().email is None
    invite = Invitation.query.filter_by(id=5).one()
    assert {u.id for u in invite.users} == {10, 11}
    assert (
        invite.used
        and invite.unlimited
        and invite.allow_downloads
        and invite.allow_live_tv
    )
    assert invite.max_active_sessions == 2
    assert [library.external_id for library in invite.libraries] == [
        "restricted-library"
    ]
    assert Connection.query.one().connection_type == "seerr"
    steps = WizardStep.query.order_by(WizardStep.position).all()
    assert "12345" in steps[2].markdown
    assert "https://requests.example.invalid" in steps[3].markdown


def test_refuses_to_merge_into_an_existing_destination(session, legacy_database):
    migrate_legacy(legacy_database)
    with pytest.raises(ValueError, match="fresh"):
        migrate_legacy(legacy_database)
    assert User.query.count() == 2
    assert Invitation.query.count() == 2


def test_converts_legacy_local_usage_time_without_changing_expiry(
    session, legacy_database
):
    migrate_legacy(legacy_database, legacy_used_timezone="Europe/Berlin")
    invite = Invitation.query.filter_by(id=5).one()
    assert invite.used_at.replace(tzinfo=UTC) == datetime(2026, 1, 1, 23, tzinfo=UTC)
    assert User.query.filter_by(id=10).one().expires.replace(tzinfo=UTC) == datetime(
        2027, 1, 1, tzinfo=UTC
    )


@pytest.mark.parametrize(
    "change",
    [
        "INSERT INTO mfa VALUES (1)",
        "UPDATE invitations SET duration='2026-01-10 00:00:00'",
        "UPDATE requests SET service='unknown'",
        "UPDATE accounts SET role='moderator'",
    ],
)
def test_unmapped_data_fails_before_any_target_write(session, legacy_database, change):
    with closing(sqlite3.connect(legacy_database)) as con:
        con.execute(change)
        con.commit()
    with pytest.raises(ValueError):
        migrate_legacy(legacy_database)
    assert User.query.count() == 0
    assert Invitation.query.count() == 0
    assert MediaServer.query.count() == 0
