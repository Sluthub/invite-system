"""Preserve Sluthub's targeted Jellyfin-to-Seerr user import."""

import requests

from app.models import Connection, User

from .base import CompanionClient


class SeerrClient(CompanionClient):
    @property
    def requires_api_call(self) -> bool:
        return True

    @property
    def display_name(self) -> str:
        return "Seerr"

    def invite_user(
        self,
        username: str,
        email: str,  # noqa: ARG002
        connection: Connection,
        password: str = "",  # noqa: ARG002
    ) -> dict[str, str]:
        if not connection.url or not connection.api_key:
            return {"status": "error", "message": "Seerr URL and API key are required"}
        users = User.query.filter_by(
            username=username, server_id=connection.media_server_id
        ).all()
        if len(users) != 1 or not users[0].token:
            return {
                "status": "error",
                "message": "The new media user was not identified",
            }
        server = connection.media_server
        if not server or server.server_type not in {"jellyfin", "emby"}:
            return {
                "status": "error",
                "message": "Seerr import requires Jellyfin or Emby",
            }
        try:
            response = requests.post(
                f"{connection.url.rstrip('/')}/api/v1/user/import-from-jellyfin",
                headers={
                    "X-Api-Key": connection.api_key,
                    "User-Agent": "SluthubInvitations/2026.9.1",
                },
                json={"jellyfinUserIds": [users[0].token]},
                timeout=10,
                allow_redirects=False,
            )
        except requests.RequestException:
            return {
                "status": "error",
                "message": "Seerr import outcome is uncertain; reconcile before retrying",
            }
        if response.status_code in {200, 201}:
            return {"status": "success", "message": "Media user imported into Seerr"}
        return {
            "status": "error",
            "message": f"Seerr import returned HTTP {response.status_code}",
        }

    def delete_user(self, username: str, connection: Connection) -> dict[str, str]:  # noqa: ARG002
        return {"status": "info_only", "message": "Seerr retains user request history"}

    def test_connection(self, connection: Connection) -> dict[str, str]:
        if not connection.url or not connection.api_key:
            return {"status": "error", "message": "Seerr URL and API key are required"}
        try:
            response = requests.get(
                f"{connection.url.rstrip('/')}/api/v1/user",
                params={"take": 1},
                headers={
                    "X-Api-Key": connection.api_key,
                    "User-Agent": "SluthubInvitations/2026.9.1",
                },
                timeout=10,
                allow_redirects=False,
            )
        except requests.RequestException:
            return {"status": "error", "message": "Seerr connection check failed"}
        return {
            "status": "success" if response.status_code == 200 else "error",
            "message": f"Seerr connection returned HTTP {response.status_code}",
        }
