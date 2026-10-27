"""Top-level Pythmon game object and state coordinator."""

from __future__ import annotations

import pygame
from pathlib import Path

from pythmon.states.overworld import OverworldState
from pythmon.states.battle import BattleState
from pythmon.save.storage import load_profile, save_profile
from pythmon.save.profile import PlayerProfile
from pythmon.states.menu import MenuState


class PythmonGame:
    """Coordinate the active game state."""

    layer = 0

    def __init__(self, input_handler: object) -> None:
        self.save_path = Path("save/profile.json")
        self.startup_message = ""
        try:
            self.profile = load_profile(self.save_path)
        except FileNotFoundError:
            self.profile = PlayerProfile()
        except (OSError, ValueError) as error:
            self.profile = PlayerProfile()
            self.startup_message = f"Save could not be loaded: {error}"
        self.overworld = OverworldState(input_handler)
        self.overworld.start_battle = self.start_battle
        self.overworld.open_menu = self.open_menu
        self.overworld.heal_party = self.profile.restore_party
        self.state = self.overworld

    def update(self, delta_time: float) -> None:
        """Advance the active game state."""
        self.state.update(delta_time)

    def draw(self, surface: pygame.Surface, camera: pygame.Vector2) -> None:
        """Draw the active game state."""
        self.state.draw(surface, camera)

    def start_battle(self, wild_encounter: bool = False) -> None:
        """Switch from the overworld to a trainer or wild battle."""
        self.state = BattleState(
            self.state.input,
            self.return_to_overworld,
            profile=self.profile,
            wild_encounter=wild_encounter,
        )

    def return_to_overworld(self) -> None:
        """Return to the existing overworld, preserving its player location."""
        self.state = self.overworld

    def open_menu(self) -> None:
        """Open the in-world menu over the existing overworld state."""
        menu = MenuState(
            self.overworld.input,
            self.overworld,
            self.profile,
            self.return_to_overworld,
            lambda: self.save(Path("save/profile.json")),
        )
        menu.message = self.startup_message
        self.startup_message = ""
        self.state = menu

    def save(self, path: Path) -> None:
        """Save the current player profile to JSON."""
        sync_profile = getattr(self.state, "sync_profile", None)
        if sync_profile is not None:
            sync_profile()
        save_profile(self.profile, path)

    def load(self, path: Path) -> None:
        """Load a player profile for future battles in this session."""
        self.profile = load_profile(path)
