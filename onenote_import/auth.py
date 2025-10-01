"""Authentication helpers for Microsoft Graph device code flow."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import msal


def _load_cache(cache_path: Path) -> msal.SerializableTokenCache:
    cache = msal.SerializableTokenCache()
    if cache_path.exists():
        cache.deserialize(cache_path.read_text())
    return cache


def _save_cache(cache: msal.SerializableTokenCache, cache_path: Path) -> None:
    cache_path.write_text(cache.serialize())


@dataclass
class DeviceCodeAuthenticator:
    """Authenticates a user via the device code flow."""

    client_id: str
    tenant_id: str = "common"
    scopes: Iterable[str] = ("https://graph.microsoft.com/.default",)
    cache_path: Path = Path("token_cache.json")

    def __post_init__(self) -> None:
        self.cache_path = Path(self.cache_path)
        self.cache = _load_cache(self.cache_path)
        authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.app = msal.PublicClientApplication(
            self.client_id, authority=authority, token_cache=self.cache
        )

    def acquire_token(self) -> dict:
        """Return a Microsoft Graph access token."""
        # Attempt silent acquisition first
        accounts = self.app.get_accounts()
        if accounts:
            result = self.app.acquire_token_silent(list(self.scopes), account=accounts[0])
            if result:
                return result

        flow = self.app.initiate_device_flow(scopes=list(self.scopes))
        if "user_code" not in flow:
            raise RuntimeError("Failed to create device code flow.")
        print(flow["message"])  # Instruct the user to authenticate.

        result = self.app.acquire_token_by_device_flow(flow)
        if "access_token" not in result:
            raise RuntimeError(
                f"Authentication failed: {result.get('error_description', result)}"
            )
        _save_cache(self.cache, self.cache_path)
        return result


__all__ = ["DeviceCodeAuthenticator"]
