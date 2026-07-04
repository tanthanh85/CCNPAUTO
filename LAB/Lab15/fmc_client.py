"""Small Cisco Secure Firewall Management Center REST API client."""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlparse

import requests
import urllib3
from dotenv import load_dotenv

load_dotenv()


class FMCError(RuntimeError):
    """Represent a controlled FMC API or configuration failure."""


class FMCClient:
    def __init__(self) -> None:
        host = os.getenv("FMC_HOST", "").strip()
        username = os.getenv("FMC_USERNAME", "").strip()
        password = os.getenv("FMC_PASSWORD", "")
        if not host or not username or not password:
            raise FMCError("FMC_HOST, FMC_USERNAME, and FMC_PASSWORD are required")

        self.base_url = f"https://{host}:{int(os.getenv('FMC_PORT', '443'))}"
        self.username = username
        self.password = password
        self.timeout = int(os.getenv("FMC_TIMEOUT", "30"))
        self.verify_tls = os.getenv("FMC_VERIFY_TLS", "false").lower() == "true"
        self.domain_uuid = os.getenv("FMC_DOMAIN_UUID", "").strip()
        self.session = requests.Session()
        self.session.verify = self.verify_tls
        self.session.headers.update({"Accept": "application/json"})
        if not self.verify_tls:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def authenticate(self) -> None:
        """Exchange Basic credentials for FMC access and refresh tokens."""
        url = self.base_url + "/api/fmc_platform/v1/auth/generatetoken"
        try:
            response = self.session.post(
                url,
                auth=(self.username, self.password),
                headers={"Content-Type": "application/json"},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise FMCError(f"FMC authentication connection failed: {exc}") from exc
        if response.status_code not in (200, 204):
            raise FMCError(f"Authentication failed with HTTP {response.status_code}")

        access_token = response.headers.get("X-auth-access-token")
        if not access_token:
            raise FMCError("FMC did not return X-auth-access-token")
        self.session.headers.update(
            {
                "X-auth-access-token": access_token,
                "Content-Type": "application/json",
            }
        )
        self.refresh_token = response.headers.get("X-auth-refresh-token", "")
        self.domain_uuid = self.domain_uuid or response.headers.get("DOMAIN_UUID", "")
        if not self.domain_uuid:
            raise FMCError("No domain UUID was configured or returned by FMC")

    def _safe_url(self, path_or_url: str) -> str:
        """Accept FMC pagination links but reject links to another origin."""
        if path_or_url.startswith("/"):
            return self.base_url + path_or_url
        parsed_expected = urlparse(self.base_url)
        parsed_actual = urlparse(path_or_url)
        if (parsed_actual.scheme, parsed_actual.netloc) != (
            parsed_expected.scheme,
            parsed_expected.netloc,
        ):
            raise FMCError("FMC pagination attempted to use a different API origin")
        return path_or_url

    def request(
        self,
        method: str,
        path_or_url: str,
        *,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
        accepted: tuple[int, ...] = (200,),
    ) -> requests.Response:
        if "X-auth-access-token" not in self.session.headers:
            self.authenticate()
        url = self._safe_url(path_or_url)
        try:
            response = self.session.request(
                method,
                url,
                params=params,
                json=payload,
                timeout=self.timeout,
            )
        except requests.Timeout as exc:
            raise FMCError(f"FMC request timed out after {self.timeout} seconds") from exc
        except requests.RequestException as exc:
            raise FMCError(f"FMC request failed: {exc}") from exc

        if response.status_code not in accepted:
            detail = response.text.replace("\n", " ")[:500]
            raise FMCError(f"HTTP {response.status_code} for {method} {url}: {detail}")
        return response

    def get_all(
        self, path: str, *, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Follow FMC paging.next links until every item is retrieved."""
        items: list[dict[str, Any]] = []
        next_url: str | None = path
        first_params = {"limit": 100, **(params or {})}
        seen: set[str] = set()
        first_page = True
        while next_url:
            absolute = self._safe_url(next_url)
            if absolute in seen:
                raise FMCError("FMC returned a repeated pagination link")
            seen.add(absolute)
            response = self.request(
                "GET", next_url, params=first_params if first_page else None
            )
            first_page = False
            body = response.json()
            items.extend(body.get("items", []))
            next_url = body.get("paging", {}).get("next")
        return items

    @property
    def domain_path(self) -> str:
        if not self.domain_uuid:
            self.authenticate()
        return f"/api/fmc_config/v1/domain/{self.domain_uuid}"

    def server_version(self) -> dict[str, Any]:
        return self.request("GET", "/api/fmc_platform/v1/info/serverversion").json()

    def devices(self) -> list[dict[str, Any]]:
        return self.get_all(self.domain_path + "/devices/devicerecords")

    def access_policies(self) -> list[dict[str, Any]]:
        return self.get_all(self.domain_path + "/policy/accesspolicies")

    def access_rules(self, policy_id: str) -> list[dict[str, Any]]:
        path = self.domain_path + f"/policy/accesspolicies/{policy_id}/accessrules"
        return self.get_all(path, params={"expanded": "true"})

    def network_objects(self, name: str = "") -> list[dict[str, Any]]:
        params = {"expanded": "true"}
        if name:
            params["filter"] = f"name:{name}"
        return self.get_all(self.domain_path + "/object/networks", params=params)

    def create_network(self, name: str, value: str) -> dict[str, Any]:
        payload = {
            "name": name,
            "value": value,
            "type": "Network",
            "description": "Created by CCNP Automation Lab 15",
        }
        response = self.request(
            "POST",
            self.domain_path + "/object/networks",
            payload=payload,
            accepted=(201,),
        )
        return response.json()

    def update_network(self, object_id: str, current: dict[str, Any], value: str) -> dict[str, Any]:
        payload = {
            "id": object_id,
            "name": current["name"],
            "value": value,
            "type": "Network",
            "description": current.get("description", "Updated by Lab 15"),
        }
        path = self.domain_path + f"/object/networks/{object_id}"
        return self.request("PUT", path, payload=payload, accepted=(200,)).json()

    def delete_network(self, object_id: str) -> None:
        path = self.domain_path + f"/object/networks/{object_id}"
        self.request("DELETE", path, accepted=(204,))
