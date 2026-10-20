from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol
import re
import unicodedata
import uuid

HERMES_REVISION = "22063fc099ec9ad8357d7f8f6e6248a0400680d3"
SUMMARY_MODEL = "anthropic/claude-haiku-5.5"
EMBEDDING_MODEL = "intfloat/multilingual-e5-small"


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def reference(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4()}"


def normalized(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).split()).casefold()


def valid_reference(value: str, prefix: str = "N") -> bool:
    return bool(re.fullmatch(rf"{prefix}-[0-9a-f]{{8}}(?:-[0-9a-f]{{4}}){{3}}-[0-9a-f]{{12}}", value))


class UserError(ValueError):
    """Error funcional seguro para presentar al usuario."""


SUMMARY_FAILURE_CODES = frozenset({
    'summary_json', 'summary_structure', 'summary_sources', 'summary_order',
    'summary_coverage', 'summary_reduction', 'summary_context',
    'summary_model_mismatch', 'summary_empty', 'summary_provider',
})


class SummaryFailure(RuntimeError):
    """Closed diagnostic codes; never carries provider output or note content."""

    def __init__(self, code):
        if code not in SUMMARY_FAILURE_CODES:
            raise ValueError('Unknown summary failure code')
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class Event:
    bot: str
    user: str
    chat: str
    message: str
    text: str

    @property
    def key(self) -> str:
        # Encoding of the tuple avoids separator collisions.
        import json
        return json.dumps([self.bot, self.chat, self.message], separators=(",", ":"))


@dataclass
class Response:
    text: str
    refs: list[str] = field(default_factory=list)
    job: str | None = None
    filename: str | None = None
    document: str | None = None
    receipt: str | None = None


class Embedder(Protocol):
    revision: str

    def encode(self, texts: list[str], *, query: bool = False) -> list[list[float]]: ...
    def chunks(self, text: str) -> list[str]: ...


class Model(Protocol):
    async def complete(self, messages: list[dict], *, max_tokens: int) -> str: ...


def display_date(value):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    return datetime.fromisoformat(value).astimezone(ZoneInfo('Europe/Madrid')).isoformat(timespec='seconds')
