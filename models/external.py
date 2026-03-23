from typing import Any

class ExternalConnection:
    def __init__(self, name: str, owner_id: str, connection_type: str) -> None:
        self.id = None
        self.owner_id = owner_id
        self.name = name
        self.connection_type = connection_type
        self.age_timestamp = None

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "name": self.name,
            "connection_type": self.connection_type,
            "age_timestamp": self.age_timestamp,
        }

    def save(self, supabase_client: Any) -> Any:
        return supabase_client.table("external_connections").insert(self.to_record()).execute()

