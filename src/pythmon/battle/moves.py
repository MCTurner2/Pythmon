"""Data model for battle moves."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Move:
    """A simple deterministic move used by a creature."""

    name: str
    power: int
    description: str
    max_uses: int = 10

    def __post_init__(self) -> None:
        if self.power <= 0:
            raise ValueError("move power must be greater than zero")
        if self.max_uses <= 0:
            raise ValueError("move max_uses must be greater than zero")
