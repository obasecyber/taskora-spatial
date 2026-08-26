from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class SourceRecord:
    source_record_id: str
    payload: dict[str, Any]


class IngestionAdapter(Protocol):
    name: str
    country_code: str

    def fetch(self) -> list[SourceRecord]: ...