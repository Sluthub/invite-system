from unittest.mock import Mock, patch

import requests

from app.extensions import db
from app.models import Connection, MediaServer, User
from app.services.companions.seerr import SeerrClient


def connection_fixture():
    server = MediaServer(
        name="Sluthub", server_type="jellyfin", url="http://media.invalid"
    )
    db.session.add(server)
    db.session.flush()
    connection = Connection(
        name="Requests",
        connection_type="seerr",
        url="https://requests.example.invalid/",
        api_key="fixture-api-key",
        media_server_id=server.id,
    )
    db.session.add(connection)
    db.session.add(
        User(
            token="media-user-id",
            username="alice",
            email="alice@example.invalid",
            code="ABCDEF",
            server_id=server.id,
        )
    )
    db.session.commit()
    return connection


def test_imports_only_the_new_user_on_the_selected_server(session):
    connection = connection_fixture()
    with patch(
        "app.services.companions.seerr.requests.post",
        return_value=Mock(status_code=201),
    ) as post:
        result = SeerrClient().invite_user("alice", "alice@example.invalid", connection)
    assert result["status"] == "success"
    post.assert_called_once_with(
        "https://requests.example.invalid/api/v1/user/import-from-jellyfin",
        headers={
            "X-Api-Key": "fixture-api-key",
            "User-Agent": "SluthubInvitations/2026.9.1",
        },
        json={"jellyfinUserIds": ["media-user-id"]},
        timeout=10,
        allow_redirects=False,
    )


def test_missing_user_does_not_trigger_an_all_user_import(session):
    connection = connection_fixture()
    with patch("app.services.companions.seerr.requests.post") as post:
        result = SeerrClient().invite_user("missing", "", connection)
    assert result["status"] == "error"
    post.assert_not_called()


def test_uncertain_import_is_not_retried_or_exposed(session):
    connection = connection_fixture()
    with patch(
        "app.services.companions.seerr.requests.post",
        side_effect=requests.Timeout("private diagnostic fixture-api-key"),
    ) as post:
        result = SeerrClient().invite_user("alice", "", connection)
    assert result["status"] == "error"
    assert "uncertain" in result["message"]
    assert "fixture-api-key" not in result["message"]
    post.assert_called_once()
