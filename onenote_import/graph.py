"""Microsoft Graph client for OneNote data."""
from __future__ import annotations

import time
from typing import Dict, Generator, Iterable, Optional

import requests


class GraphClient:
    """Lightweight wrapper around the Microsoft Graph OneNote endpoints."""

    base_url = "https://graph.microsoft.com/v1.0"

    def __init__(self, access_token: str, request_timeout: int = 30) -> None:
        self._access_token = access_token
        self._timeout = request_timeout

    # generic
    def _paginate(self, url: str, params: Optional[Dict] = None) -> Generator[dict, None, None]:
        while url:
            response = requests.get(
                url,
                headers={"Authorization": f"Bearer {self._access_token}"},
                params=params,
                timeout=self._timeout,
            )
            response.raise_for_status()
            data = response.json()
            for item in data.get("value", []):
                yield item
            url = data.get("@odata.nextLink")
            params = None  # already included in nextLink

    def iter_sections(self) -> Iterable[dict]:
        """Yield all sections available to the current user."""
        url = f"{self.base_url}/me/onenote/sections"
        return self._paginate(url)

    def iter_pages(self, section_id: str) -> Iterable[dict]:
        """Yield all pages belonging to a section."""
        url = f"{self.base_url}/me/onenote/sections/{section_id}/pages"
        return self._paginate(url)

    def get_page_content(self, page_id: str) -> str:
        url = f"{self.base_url}/me/onenote/pages/{page_id}/content"
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {self._access_token}"},
            timeout=self._timeout,
        )
        response.raise_for_status()
        return response.text


__all__ = ["GraphClient"]
