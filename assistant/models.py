"""Small contracts shared by routing, dispatch and response stages."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Intent:
    name: str
    payload: str | None = None


@dataclass(frozen=True)
class Response:
    text: str = ""
    continue_running: bool = True


@dataclass
class Session:
    pending_action: str | None = None


class CommandUnavailableError(RuntimeError):
    """Expected feature restriction whose explanation should reach the user."""
