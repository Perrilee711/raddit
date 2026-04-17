from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ToolResult:
    ok: bool
    message: str
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ResourceDocument:
    uri: str
    title: str
    mime_type: str
    data: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
