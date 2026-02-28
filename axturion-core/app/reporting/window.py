from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ReportingWindow:
    from_datetime: datetime | None
    to_datetime: datetime | None

    def __post_init__(self) -> None:
        self.validate()

    def is_active(self) -> bool:
        return self.from_datetime is not None or self.to_datetime is not None

    @staticmethod
    def all_time() -> "ReportingWindow":
        return ReportingWindow(from_datetime=None, to_datetime=None)

    def validate(self) -> None:
        if self.from_datetime is None or self.to_datetime is None:
            return
        if self.from_datetime >= self.to_datetime:
            raise ValueError("from_datetime must be before to_datetime")
