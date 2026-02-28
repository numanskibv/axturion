from __future__ import annotations

from typing import Literal, TypeAlias

Language: TypeAlias = Literal["en", "nl"]

ALLOWED_LANGUAGES: set[Language] = {"en", "nl"}
DEFAULT_LANGUAGE: Language = "en"


def resolve_language(
    *, org_default: Language, user_override: Language | None
) -> Language:
    return user_override or org_default
