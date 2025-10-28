from dataclasses import dataclass
from typing import Any

@dataclass
class CachedResult:
    result: Any
    timestamp: float
