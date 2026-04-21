import json
from urllib import request
from typing import Any


class External:
    def __init__(
        self,
        id: str | None,
        owner_id: str,
        url: str,
        provider: str,
        supabase_client: Any,
        user_id: str | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
    ) -> None:
        self.id = id
        self.owner_id = owner_id
        self.url = url
        self.provider = provider
        self.user_id = user_id
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.supabase_client = supabase_client

    def to_record(self) -> dict[str, Any]:
        # this builds a dict of all the fields on this object
        # we need this when saving to the database
        # the keys have to match the column names in the externals table
        rec = {
            "id": self.id, #the id of this external
            "owner_id": self.owner_id,
            "url": self.url,
            "provider": self.provider,
            "user_id": self.user_id,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
        }
        # return the dict so the caller can use it
        return rec


    def save(self) -> Any:
        record = self.to_record() #get the record dict first
        return self.supabase_client.table("externals").insert(record).execute()

    def request_json(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        hdrs = {"Content-Type": "application/json"}
        # add the auth header if we have a token stored
        if self.access_token is not None and len(self.access_token) > 0:
            hdrs["Authorization"] = f"Bearer {self.access_token}"

        fullUrl = f"{self.url.rstrip('/')}{path}"
        reqBody = json.dumps(payload).encode("utf-8") if payload else None

        req = request.Request(fullUrl, data=reqBody, method=method.upper(), headers=hdrs)
        with request.urlopen(req) as response:
            rawData = response.read().decode("utf-8")
            if len(rawData) > 0:
                return json.loads(rawData)
            return None
