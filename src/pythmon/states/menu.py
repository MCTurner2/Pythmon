"""In-world pause menu for player information and session actions."""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from pathlib import Path

import pygame

from pythmon.save.profile import PlayerProfile


class WorldMenu(str, Enum):
    """Screens available from the overworld menu."""

    COMMANDS = "commands"
    TEAM = "team"
    PACK = "pack"


class MenuState:
    """Pause the overworld while showing profile, item, and save actions."""

    def __init__(
        self,
        input_handler: object,
        underlying: object,
        profile: PlayerProfile,
        on_resume: Callable[[], None],
        on_save: Callable[[], None],
    ) -> None:
        self.input = input_handler
        self.underlying = underlying
        self.profile = profile
        self.on_resume = on_resume
        self.on_save = on_save
        self.menu = WorldMenu.COMMANDS
        self.menu_index = 0
        self.team_index = profile.active_index
        self.message = ""
        self.font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 25)

    def update(self, _delta_time: float) -> None:
        """Handle menu navigation while the overworld remains paused."""
        del _delta_time
        if self.menu is WorldMenu.COMMANDS:
            self._update_commands()
        elif self.menu is WorldMenu.PACK:
            self._update_pack()
        else:
            self._update_subscreen()

    def _update_commands(self) -> None:
        if self.input.is_key_pressed(pygame.K_ESCAPE):
            self.on_resume()
        elif self.input.is_key_pressed(pygame.K_UP):
            self.menu_index = (self.menu_index - 1) % 4
        elif self.input.is_key_pressed(pygame.K_DOWN):
            self.menu_index = (self.menu_index + 1) % 4
        elif self.input.is_key_pressed(pygame.K_RETURN) or self.input.is_key_pressed(
            pygame.K_SPACE
        ):
            if self.menu_index == 0:
                self.menu = WorldMenu.TEAM
            elif self.menu_index == 1:
                self.menu = WorldMenu.PACK
            elif self.menu_index == 2:
                try:
                    self.on_save()
                except OSError as error:
                    self.message = f"Save failed: {error}"
                else:
                    self.message = "Game saved."
            else:
                self.on_resume()

    def _update_pack(self) -> None:
        if self.input.is_key_pressed(pygame.K_ESCAPE):
            self.menu = WorldMenu.COMMANDS
            self.menu_index = 0
        elif self.input.is_key_pressed(pygame.K_RETURN) or self.input.is_key_pressed(
            pygame.K_SPACE
        ):
            if self.profile.heal_active_creature():
                self.message = f"{self.profile.active_creature.name} recovered 10 HP."
            else:
                self.message = "No Heal Patch can be used right now."

    def _update_subscreen(self) -> None:
        if self.menu is WorldMenu.TEAM:
            if self.input.is_key_pressed(pygame.K_UP):
                self.team_index = (self.team_index - 1) % len(self.profile.party)
            elif self.input.is_key_pressed(pygame.K_DOWN):
                self.team_index = (self.team_index + 1) % len(self.profile.party)
            elif self.input.is_key_pressed(pygame.K_RETURN) or self.input.is_key_pressed(
                pygame.K_SPACE
            ):
                self.profile.set_active_creature(self.team_index)
                self.message = (
                    f"{self.profile.active_creature.name} is now in front."
                )
            elif self.input.is_key_pressed(pygame.K_ESCAPE):
                self.menu = WorldMenu.COMMANDS
                self.menu_index = 0
            return

        if self.input.is_key_pressed(pygame.K_ESCAPE) or self.input.is_key_pressed(
            pygame.K_RETURN
        ) or self.input.is_key_pressed(pygame.K_SPACE):
            self.menu = WorldMenu.COMMANDS
            self.menu_index = 0

    def draw(self, surface: pygame.Surface, camera: pygame.Vector2) -> None:
        """Draw the paused overworld and the menu overlay."""
        self.underlying.draw(surface, camera)
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((8, 12, 20, 150))
        surface.blit(overlay, (0, 0))

        panel = pygame.Rect(
            surface.get_width() - 410 if self.menu is WorldMenu.COMMANDS else 80,
            60,
            330 if self.menu is WorldMenu.COMMANDS else surface.get_width() - 160,
            600,
        )
        pygame.draw.rect(surface, (20, 24, 36), panel, border_radius=10)
        pygame.draw.rect(surface, (232, 232, 210), panel, 3, border_radius=10)
        if self.menu is WorldMenu.COMMANDS:
            self._draw_commands(surface, panel)
        elif self.menu is WorldMenu.TEAM:
            self._draw_team(surface, panel)
        else:
            self._draw_pack(surface, panel)

    def _draw_commands(self, surface: pygame.Surface, panel: pygame.Rect) -> None:
        self._text(surface, "PYTHMON MENU", (panel.x + 30, panel.y + 28), self.font)
        commands = ("Team", "Pack", "Save", "Resume")
        for index, command in enumerate(commands):
            color = (255, 230, 100) if index == self.menu_index else (245, 245, 235)
            self._text(
                surface,
                f"{'> ' if index == self.menu_index else '  '}{command}",
                (panel.x + 35, panel.y + 100 + index * 52),
                self.font,
                color,
            )
        self._text(surface, "Up/Down  Enter  Esc", (panel.x + 30, panel.bottom - 42), self.small_font)
        self._draw_message(surface, panel)

    def _draw_team(self, surface: pygame.Surface, panel: pygame.Rect) -> None:
        self._text(surface, "TEAM", (panel.x + 30, panel.y + 28), self.font)
        selected = self.profile.party[self.team_index]
        list_width = 300
        for index, creature in enumerate(self.profile.party):
            marker = "*" if index == self.profile.active_index else " "
            color = (255, 230, 100) if index == self.team_index else (245, 245, 235)
            self._text(
                surface,
                f"{'> ' if index == self.team_index else '  '}{marker}{creature.name}",
                (panel.x + 35, panel.y + 105 + index * 48),
                self.font,
                color,
            )
        card = pygame.Rect(panel.x + list_width + 30, panel.y + 80, panel.width - list_width - 60, 390)
        pygame.draw.rect(surface, (30, 38, 54), card, border_radius=8)
        pygame.draw.rect(surface, (110, 150, 180), card, 2, border_radius=8)
        self._draw_creature_summary(surface, card, selected)
        self._text(
            surface,
            "Up/Down: Select  Enter: Set active  Esc: Back",
            (panel.x + 30, panel.bottom - 42),
            self.small_font,
        )
        self._draw_message(surface, panel)

    def _draw_creature_summary(
        self,
        surface: pygame.Surface,
        card: pygame.Rect,
        creature: object,
    ) -> None:
        """Draw a placeholder portrait plus readable creature details."""
        center = (card.centerx, card.y + 82)
        pygame.draw.circle(surface, (95, 125, 190), center, 48)
        pygame.draw.circle(surface, (155, 190, 235), center, 34, 3)
        self._text(surface, "</>", (center[0] - 25, center[1] - 13), self.font)
        self._text(surface, creature.name, (card.x + 18, card.y + 145), self.font)
        self._text(
            surface,
            f"Level {creature.level}   HP {creature.current_hp}/{creature.max_hp}",
            (card.x + 18, card.y + 180),
            self.small_font,
        )
        self._text(surface, "STATS", (card.x + 18, card.y + 220), self.small_font, (150, 200, 220))
        self._text(
            surface,
            f"Attack  {creature.attack}    Defense  {creature.defense}",
            (card.x + 18, card.y + 248),
            self.small_font,
        )
        self._text(surface, "MOVES", (card.x + 18, card.y + 288), self.small_font, (150, 200, 220))
        for index, move in enumerate(creature.moves):
            remaining = self.profile.move_uses.get(
                f"{self.profile.active_index}:{move.name}",
                move.max_uses,
            )
            self._text(
                surface,
                f"{index + 1}. {move.name}  "
                f"{remaining}/{move.max_uses} uses  ({move.power} power)",
                (card.x + 18, card.y + 316 + index * 25),
                self.small_font,
            )

    def _draw_pack(self, surface: pygame.Surface, panel: pygame.Rect) -> None:
        count = self.profile.inventory.get("Heal Patch", 0)
        self._text(surface, "PACK", (panel.x + 30, panel.y + 28), self.font)
        self._text(surface, f"> Heal Patch x{count}  (+10 HP)", (panel.x + 55, panel.y + 105), self.font, (255, 230, 100))
        self._text(surface, "Enter: Use   Esc: Back", (panel.x + 30, panel.bottom - 42), self.small_font)
        self._draw_message(surface, panel)

    def _draw_message(self, surface: pygame.Surface, panel: pygame.Rect) -> None:
        if self.message:
            self._text(
                surface,
                self.message,
                (panel.x + 20, panel.y + 390),
                self.small_font,
            )

    def _text(
        self,
        surface: pygame.Surface,
        text: str,
        position: tuple[int, int],
        font: pygame.font.Font,
        color: tuple[int, int, int] = (245, 245, 235),
    ) -> None:
        surface.blit(font.render(text, True, color), position)
