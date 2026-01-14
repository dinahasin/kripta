from dataclasses import dataclass, asdict
import json
import time
from typing import Optional

@dataclass
class PasswordEntry:
    id: str
    title: str
    username: str
    password: str
    url: str
    notes: str
    created_at: int
    updated_at: int

    @classmethod
    def create(cls, id: str, title: str, username: str, password: str, url: str = "", notes: str = "") -> 'PasswordEntry':
        now = int(time.time())
        return cls(
            id=id,
            title=title,
            username=username,
            password=password,
            url=url,
            notes=notes,
            created_at=now,
            updated_at=now
        )
    
    def to_bytes(self) -> bytes:
        """Serializes the entry to a JSON byte string."""
        return json.dumps(asdict(self)).encode('utf-8')

    @classmethod
    def from_bytes(cls, data: bytes) -> 'PasswordEntry':
        """Deserializes from a JSON byte string."""
        d = json.loads(data.decode('utf-8'))
        return cls(**d)
