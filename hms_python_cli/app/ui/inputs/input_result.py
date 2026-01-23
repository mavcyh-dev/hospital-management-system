from dataclasses import dataclass
from typing import Any


@dataclass
class InputResult:
    value: Any
    display_value: str | None = None
    error: str | None = None
