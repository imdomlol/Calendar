import json
from typing import Any
from urllib import request


class External:
    def __init__(
        self,
        id: str | None,
        url: str,
        provider: str,
        supabase_client: Any,
        user_id: str | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
    ) -> None:
        self.id = id
        self.url = url
        self.provider = provider
        self.user_id = user_id
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.supabase_client = supabase_client

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "url": self.url,
            "provider": self.provider,
            "user_id": self.user_id,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
        }

    def save(self) -> Any:
        record = self.to_record()
        return self.supabase_client.table("externals").insert(record).execute()

    def request_json(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        url = f"{self.url.rstrip('/')}{path}"
        body = json.dumps(payload).encode("utf-8") if payload else None

        req = request.Request(url, data=body, method=method.upper(), headers=headers)
        with request.urlopen(req) as response:
            raw = response.read().decode("utf-8")
            if raw:
                return json.loads(raw)
            return None
