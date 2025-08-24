import os
from typing import Any, Dict, List, Optional

import httpx


class ApiClient:
    def __init__(self) -> None:
        self.base_url = os.getenv("API_BASE_URL", "").rstrip("/")

    def enabled(self) -> bool:
        return bool(self.base_url)

    def _url(self, path: str) -> str:
        if not self.enabled():
            raise RuntimeError("API_BASE_URL is not configured")
        return f"{self.base_url}{path}"

    def list_news(self) -> List[Dict[str, Any]]:
        with httpx.Client(timeout=10) as client:
            r = client.get(self._url("/news"))
            r.raise_for_status()
            return r.json()

    def create_news(self, data: Dict[str, Any]) -> Dict[str, Any]:
        with httpx.Client(timeout=10) as client:
            r = client.post(self._url("/news"), json=data)
            r.raise_for_status()
            return r.json()

    def update_news(self, doc_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        with httpx.Client(timeout=10) as client:
            r = client.put(self._url(f"/news/{doc_id}"), json=data)
            r.raise_for_status()
            return r.json()

    def delete_news(self, doc_id: str) -> None:
        with httpx.Client(timeout=10) as client:
            r = client.delete(self._url(f"/news/{doc_id}"))
            r.raise_for_status()






