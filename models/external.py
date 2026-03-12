import json
import os
from datetime import datetime, timezone
from typing import Any
from urllib import request


class External:
    def __init__(
        self,
        name: str,
        url: str,
        supabase_client: Any,
        provider: str = "custom",
        user_id: str | None = None,
        account_identifier: str | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
        token_expires_at: str | None = None,
        scopes: list[str] | None = None,
        credentials: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        default_resource_id: str = "primary",
        google_credentials: Any = None,
    ) -> None:
        self.id = None  # Will be set when this connection is saved to the database
        self.name = name
        self.url = url
        self.provider = provider
        self.user_id = user_id
        self.account_identifier = account_identifier
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_expires_at = token_expires_at
        self.scopes = scopes or []
        self.credentials = credentials or {}
        self.metadata = metadata or {}
        self.default_resource_id = default_resource_id
        self.status = "connected"

        self.supabase_client = supabase_client
        self.age_timestamp = None  # May be returned by DB on insert

        # Backward-compatible alias used by earlier Google-only version.
        self.google_credentials = google_credentials
        self._provider_clients: dict[str, Any] = {}

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "provider": self.provider,
            "user_id": self.user_id,
            "account_identifier": self.account_identifier,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_expires_at": self.token_expires_at,
            "scopes": self.scopes,
            "credentials": self.credentials,
            "metadata": self.metadata,
            "default_resource_id": self.default_resource_id,
            "status": self.status,
            "age_timestamp": self.age_timestamp,
        }

    def save(self) -> Any:
        record = self.to_record()
        return self.supabase_client.table("externals").insert(record).execute()

    def edit(self, **kwargs: Any) -> Any:
        if self.id is None:
            raise ValueError("External connection must be saved before edited.")

        current = self.to_record()
        for key, value in kwargs.items():
            if key in current:
                setattr(self, key, value)

        return self.supabase_client.table("externals").update(self.to_record()).match({"id": self.id}).execute()

    def remove(self) -> Any:
        if self.id is None:
            raise ValueError("External connection must be saved before removed.")

        return self.supabase_client.table("externals").delete().match({"id": self.id}).execute()

    def set_tokens(
        self,
        access_token: str,
        refresh_token: str | None = None,
        token_expires_at: str | None = None,
    ) -> None:
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_expires_at = token_expires_at

    def is_token_expired(self) -> bool:
        if not self.token_expires_at:
            return False

        try:
            return datetime.fromisoformat(self.token_expires_at) <= datetime.now(timezone.utc)
        except ValueError:
            return False

    def connect(self) -> None:
        self.status = "connected"

    def disconnect(self) -> None:
        self.status = "disconnected"

    def _auth_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def request_json(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        query: str = "",
        headers: dict[str, str] | None = None,
    ) -> Any:
        base = self.url.rstrip("/")
        final_path = path if path.startswith("/") else f"/{path}"
        full_url = f"{base}{final_path}{query}"

        merged_headers = self._auth_headers()
        if headers:
            merged_headers.update(headers)

        body = None
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")

        req = request.Request(full_url, data=body, method=method.upper(), headers=merged_headers)
        with request.urlopen(req) as response:
            content_type = response.headers.get("Content-Type", "")
            raw = response.read().decode("utf-8")
            if "application/json" in content_type and raw:
                return json.loads(raw)
            return raw

    def fetch_data(self, resource: str, **kwargs: Any) -> Any:
        if self.provider == "google_calendar":
            return self._fetch_google(resource=resource, **kwargs)

        raise NotImplementedError(f"Provider '{self.provider}' is not implemented for fetch_data().")

    def distribute_data(self, resource: str, payload: dict[str, Any], **kwargs: Any) -> Any:
        if self.provider == "google_calendar":
            return self._push_google(resource=resource, payload=payload, **kwargs)

        raise NotImplementedError(f"Provider '{self.provider}' is not implemented for distribute_data().")

    def _build_google_service(self) -> Any:
        if "google_calendar" in self._provider_clients:
            return self._provider_clients["google_calendar"]

        credentials = self.google_credentials

        if credentials is None and self.credentials:
            try:
                from google.oauth2.credentials import Credentials
            except ModuleNotFoundError as exc:
                raise RuntimeError(
                    "Missing Google auth package. Install requirements or run: "
                    "python -m pip install google-auth google-api-python-client"
                ) from exc

            credentials = Credentials(
                token=self.access_token or self.credentials.get("access_token"),
                refresh_token=self.refresh_token or self.credentials.get("refresh_token"),
                token_uri=self.credentials.get("token_uri"),
                client_id=self.credentials.get("client_id"),
                client_secret=self.credentials.get("client_secret"),
                scopes=self.scopes or self.credentials.get("scopes"),
            )

        if credentials is None:
            service_account_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if not service_account_path:
                raise RuntimeError(
                    "Google credentials not set. Provide google credentials in this object, "
                    "or set GOOGLE_APPLICATION_CREDENTIALS for service-account access."
                )

            try:
                from google.oauth2 import service_account
            except ModuleNotFoundError as exc:
                raise RuntimeError(
                    "Missing Google auth package. Install requirements or run: "
                    "python -m pip install google-auth google-api-python-client"
                ) from exc

            credentials = service_account.Credentials.from_service_account_file(
                service_account_path,
                scopes=self.scopes or ["https://www.googleapis.com/auth/calendar"],
            )

        try:
            from googleapiclient.discovery import build
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Missing Google API package. Install requirements or run: "
                "python -m pip install google-api-python-client"
            ) from exc

        service = build("calendar", "v3", credentials=credentials)
        self._provider_clients["google_calendar"] = service
        return service

    def _fetch_google(self, resource: str, **kwargs: Any) -> Any:
        service = self._build_google_service()
        calendar_id = kwargs.get("calendar_id", self.default_resource_id)

        if resource == "calendars":
            response = service.calendarList().list().execute()
            return response.get("items", [])

        if resource == "events":
            max_results = kwargs.get("max_results", 10)
            time_min = kwargs.get("time_min") or datetime.now(timezone.utc).isoformat()
            response = (
                service.events()
                .list(
                    calendarId=calendar_id,
                    timeMin=time_min,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            return response.get("items", [])

        if resource == "event":
            event_id = kwargs.get("event_id")
            if not event_id:
                raise ValueError("event_id is required when resource='event'.")
            return service.events().get(calendarId=calendar_id, eventId=event_id).execute()

        raise ValueError(f"Unsupported Google fetch resource: {resource}")

    def _push_google(self, resource: str, payload: dict[str, Any], **kwargs: Any) -> Any:
        service = self._build_google_service()
        calendar_id = kwargs.get("calendar_id", self.default_resource_id)

        if resource == "event.create":
            return service.events().insert(calendarId=calendar_id, body=payload).execute()

        if resource == "event.update":
            event_id = kwargs.get("event_id")
            if not event_id:
                raise ValueError("event_id is required when resource='event.update'.")
            return (
                service.events()
                .update(calendarId=calendar_id, eventId=event_id, body=payload)
                .execute()
            )

        if resource == "event.delete":
            event_id = kwargs.get("event_id")
            if not event_id:
                raise ValueError("event_id is required when resource='event.delete'.")
            return service.events().delete(calendarId=calendar_id, eventId=event_id).execute()

        raise ValueError(f"Unsupported Google distribution resource: {resource}")

    # Backward-compatible wrappers from the earlier Google-only version.
    def list_calendars(self) -> list[dict[str, Any]]:
        return self.fetch_data("calendars")

    def list_upcoming_events(
        self,
        max_results: int = 10,
        time_min: str | None = None,
    ) -> list[dict[str, Any]]:
        return self.fetch_data("events", max_results=max_results, time_min=time_min)

    def get_event(self, event_id: str) -> dict[str, Any]:
        return self.fetch_data("event", event_id=event_id)
