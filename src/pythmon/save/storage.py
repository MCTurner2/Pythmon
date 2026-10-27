"""JSON persistence for player profiles."""

from __future__ import annotations

import json
from pathlib import Path

from pythmon.save.profile import PlayerProfile


def save_profile(profile: PlayerProfile, path: Path) -> None:
    """Write a profile as readable, versioned JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(profile.to_dict(), indent=2) + "\n",
        encoding="utf-8",
    )


def load_profile(path: Path) -> PlayerProfile:
    """Load a profile and surface malformed save data to the caller."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid profile JSON: {path}") from error
    if not isinstance(data, dict):
        raise ValueError("profile root must be an object")
    return PlayerProfile.from_dict(data)
