"""Playable Pygame battle presentation."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

import pygame

from pythmon.battle.factories import create_trainer_battle, create_wild_battle
from pythmon.save.profile import PlayerProfile


@dataclass(frozen=True)
class BattleEffects:
    """Optional hooks for game-specific animation and sound implementations."""

    play_attack_animation: Callable[[str, str], None] | None = None
    play_sound: Callable[[str], None] | None = None


class BattlePhase(str, Enum):
    """Presentation phases used to sequence a battle turn."""

    READY = "ready"
    PLAYER_ATTACK = "player_attack"
    ENEMY_ATTACK = "enemy_attack"
    RESULT = "result"
    COMPLETE = "complete"


class BattleMenu(str, Enum):
    """Menus available while the player is choosing a battle action."""

    COMMANDS = "commands"
    MOVES = "moves"
    PACK = "pack"
    TEAM = "team"


class BattleState:
    """Render a battle and resolve actions selected from keyboard menus."""

    ENEMY_TURN_DELAY = 0.7
    ATTACK_ANIMATION_DURATION = 0.35
    RESULT_DELAY = 0.8

    def __init__(
        self,
        input_handler: object,
        on_finished: Callable[[], None],
        effects: BattleEffects | None = None,
        wild_encounter: bool = False,
        profile: PlayerProfile | None = None,
    ) -> None:
        self.input = input_handler
        self.on_finished = on_finished
        self.profile = profile or PlayerProfile()
        self.battle = (
            create_wild_battle(self.profile)
            if wild_encounter
            else create_trainer_battle(self.profile)
        )
        self.effects = effects or BattleEffects()
        self.wild_encounter = wild_encounter
        self.menu = BattleMenu.COMMANDS
        self.menu_index = 0
        self.menu_message = ""
        self.phase = BattlePhase.READY
        self.pause_remaining = 0.0
        self.enemy_turn_pending = False
        self.result_pending = False
        self.animation_elapsed = 0.0
        self.flash_remaining = 0.0
        self.shake_remaining = 0.0
        self.shake_direction = 1
        self.pending_move = None
        self.pending_damage = 0
        self.display_player_hp = float(self.battle.player.current_hp)
        self.display_enemy_hp = float(self.battle.enemy.current_hp)
        self.starting_target_hp = 0.0
        self.target_hp = 0.0
        self.hp_animation_active = False
        self.font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 25)

    def update(self, _delta_time: float) -> None:
        """Select a move with 1 or 2 and return after the result is acknowledged."""
        self._update_feedback(_delta_time)
        if self.pause_remaining > 0:
            self.pause_remaining = max(0.0, self.pause_remaining - _delta_time)
            if self.pause_remaining > 1e-6:
                return
            if self.phase is BattlePhase.PLAYER_ATTACK:
                self.battle.apply_player_move(self.pending_move, self.pending_damage)
                self._sync_profile_move_uses()
                self.display_enemy_hp = float(self.target_hp)
                self.pending_move = None
                self.hp_animation_active = False
                self.phase = BattlePhase.ENEMY_ATTACK
                if self.battle.finished:
                    self.result_pending = True
                    self.phase = BattlePhase.RESULT
                    self.pause_remaining = self.RESULT_DELAY
                else:
                    self.enemy_turn_pending = True
                    self.pause_remaining = self.ENEMY_TURN_DELAY
                return
            if self.enemy_turn_pending:
                self.enemy_turn_pending = False
                self.phase = BattlePhase.ENEMY_ATTACK
                self.animation_elapsed = 0.0
                self._play_attack_effects(
                    self.battle.enemy.name,
                    self.battle.enemy.moves[0].name,
                )
                self.pending_damage = self.battle.enemy_move_damage()
                self.starting_target_hp = self.display_player_hp
                self.target_hp = float(
                    max(0, self.battle.player.current_hp - self.pending_damage)
                )
                self.battle.apply_enemy_move(
                    self.battle.enemy.moves[0],
                    self.pending_damage,
                )
                self.hp_animation_active = True
                self.animation_elapsed = 0.0
                if self.battle.finished:
                    self.result_pending = True
                    self.phase = BattlePhase.RESULT
                    self.pause_remaining = self.RESULT_DELAY
                else:
                    self.pause_remaining = self.ATTACK_ANIMATION_DURATION
                return
            if self.phase is BattlePhase.ENEMY_ATTACK:
                self.phase = BattlePhase.READY
                self.menu = BattleMenu.COMMANDS
                self.menu_index = 0
                return
            elif self.result_pending:
                self.result_pending = False
                self.phase = BattlePhase.COMPLETE
            return

        if self.battle.finished:
            if self.result_pending:
                return
            if self.input.is_key_pressed(pygame.K_RETURN) or self.input.is_key_pressed(
                pygame.K_SPACE
            ):
                self.on_finished()
            return

        if self.menu is BattleMenu.COMMANDS:
            self._update_command_menu()
        elif self.menu is BattleMenu.MOVES:
            self._update_move_menu()
        else:
            self._update_submenu()

    def _update_command_menu(self) -> None:
        """Handle the outer battle command menu."""
        command_count = 4
        if self.input.is_key_pressed(pygame.K_UP):
            self.menu_index = (self.menu_index - 2) % command_count
        elif self.input.is_key_pressed(pygame.K_DOWN):
            self.menu_index = (self.menu_index + 2) % command_count
        elif self.input.is_key_pressed(pygame.K_LEFT):
            self.menu_index = (self.menu_index - 1) % command_count
        elif self.input.is_key_pressed(pygame.K_RIGHT):
            self.menu_index = (self.menu_index + 1) % command_count
        elif self.input.is_key_pressed(pygame.K_RETURN) or self.input.is_key_pressed(
            pygame.K_SPACE
        ):
            if self.menu_index == 0:
                self.menu = BattleMenu.MOVES
                self.menu_index = 0
                self.menu_message = ""
            elif self.menu_index == 1:
                self.menu = BattleMenu.PACK
                self.menu_index = 0
                self.menu_message = ""
            elif self.menu_index == 2:
                self.menu = BattleMenu.TEAM
                self.menu_index = 0
                self.menu_message = ""
            elif self.menu_index == 3:
                if self.wild_encounter:
                    self.battle.finished = True
                    self.battle.message = "You got away safely!"
                    self.result_pending = True
                    self.phase = BattlePhase.RESULT
                    self.pause_remaining = self.RESULT_DELAY
                else:
                    self.menu_message = "You cannot run from a trainer battle."

    def _update_move_menu(self) -> None:
        """Handle move selection and return to commands with Escape."""
        move_count = len(self.battle.player.moves)
        if self.input.is_key_pressed(pygame.K_ESCAPE):
            self.menu = BattleMenu.COMMANDS
            self.menu_index = 0
        elif self.input.is_key_pressed(pygame.K_UP):
            self.menu_index = (self.menu_index - 2) % move_count
        elif self.input.is_key_pressed(pygame.K_DOWN):
            self.menu_index = (self.menu_index + 2) % move_count
        elif self.input.is_key_pressed(pygame.K_LEFT):
            self.menu_index = (self.menu_index - 1) % move_count
        elif self.input.is_key_pressed(pygame.K_RIGHT):
            self.menu_index = (self.menu_index + 1) % move_count
        elif self.input.is_key_pressed(pygame.K_RETURN) or self.input.is_key_pressed(
            pygame.K_SPACE
        ):
            self._select_move(self.menu_index)

    def _update_submenu(self) -> None:
        """Use a Heal Patch or return from a party screen."""
        if self.input.is_key_pressed(pygame.K_ESCAPE):
            self.menu = BattleMenu.COMMANDS
            self.menu_index = 0
        elif self.menu is BattleMenu.TEAM and self.input.is_key_pressed(
            pygame.K_UP
        ):
            self.menu_index = (self.menu_index - 1) % len(self.profile.party)
        elif self.menu is BattleMenu.TEAM and self.input.is_key_pressed(
            pygame.K_DOWN
        ):
            self.menu_index = (self.menu_index + 1) % len(self.profile.party)
        elif self.menu is BattleMenu.PACK and (
            self.input.is_key_pressed(pygame.K_RETURN)
            or self.input.is_key_pressed(pygame.K_SPACE)
        ):
            if self.profile.heal_active_creature():
                self.menu_message = (
                    f"{self.profile.active_creature.name} recovered 10 HP!"
                )
                self.battle.message = self.menu_message
                self.starting_target_hp = self.display_player_hp
                self.target_hp = float(self.battle.player.current_hp)
                self.animation_elapsed = 0.0
                self.hp_animation_active = True
                self.enemy_turn_pending = True
                self.pause_remaining = self.ENEMY_TURN_DELAY
            else:
                self.menu_message = "No Heal Patch can be used right now."
        elif self.menu is BattleMenu.TEAM and (
            self.input.is_key_pressed(pygame.K_RETURN)
            or self.input.is_key_pressed(pygame.K_SPACE)
        ):
            self._select_battle_creature()

    def _select_battle_creature(self) -> None:
        """Switch active battle creature and give the opponent a turn."""
        index = self.menu_index
        creature = self.profile.party[index]
        if index == self.profile.active_index:
            self.menu_message = f"{creature.name} is already in battle."
            return
        if creature.defeated:
            self.menu_message = f"{creature.name} has no HP left."
            return
        self._sync_profile_move_uses()
        self.profile.set_active_creature(index)
        self.battle.player = creature
        self.battle.move_uses.update(self.profile.active_move_uses())
        self.display_player_hp = float(creature.current_hp)
        self.menu = BattleMenu.COMMANDS
        self.menu_index = 0
        self.battle.message = f"Go, {creature.name}!"
        self.enemy_turn_pending = True
        self.pause_remaining = self.ENEMY_TURN_DELAY

    def _select_move(self, index: int) -> None:
        """Start the selected move's presentation sequence."""
        move = self.battle.player.moves[index]
        if not self.battle.consume_move(move):
            self.menu_message = f"{move.name} has no uses left."
            self.battle.message = self.menu_message
            return
        self._play_attack_effects(self.battle.player.name, move.name)
        self.pending_move = move
        self.pending_damage = self.battle.player_move_damage(move)
        self.starting_target_hp = self.display_enemy_hp
        self.target_hp = float(max(0, self.battle.enemy.current_hp - self.pending_damage))
        self.phase = BattlePhase.PLAYER_ATTACK
        self.animation_elapsed = 0.0
        self.hp_animation_active = True
        self.flash_remaining = self.ATTACK_ANIMATION_DURATION
        self.shake_remaining = self.ATTACK_ANIMATION_DURATION
        self.pause_remaining = self.ATTACK_ANIMATION_DURATION

    def _sync_profile_move_uses(self) -> None:
        """Persist current player move uses in the session profile."""
        self.profile.update_active_move_uses(
            {
                move: self.battle.remaining_uses(move)
                for move in self.battle.player.moves
            }
        )

    def sync_profile(self) -> None:
        """Expose save synchronization to the game coordinator."""
        self._sync_profile_move_uses()

    def _play_attack_effects(self, creature_name: str, move_name: str) -> None:
        """Dispatch animation and sound events without requiring assets."""
        if self.effects.play_attack_animation is not None:
            self.effects.play_attack_animation(creature_name, move_name)
        if self.effects.play_sound is not None:
            self.effects.play_sound(f"move:{move_name}")

    def _update_feedback(self, delta_time: float) -> None:
        """Advance placeholder flash and shake effects."""
        if self.hp_animation_active:
            self.animation_elapsed += delta_time
        self.flash_remaining = max(0.0, self.flash_remaining - delta_time)
        self.shake_remaining = max(0.0, self.shake_remaining - delta_time)
        if self.hp_animation_active:
            progress = min(
                self.animation_elapsed / self.ATTACK_ANIMATION_DURATION,
                1.0,
            )
            displayed = self.starting_target_hp + (
                self.target_hp - self.starting_target_hp
            ) * progress
            if self.phase is BattlePhase.PLAYER_ATTACK:
                self.display_enemy_hp = displayed
            else:
                self.display_player_hp = displayed
        if self.shake_remaining > 0:
            self.shake_direction *= -1

    def draw(self, surface: pygame.Surface, _camera: pygame.Vector2) -> None:
        """Draw the battle arena, creatures, health bars, and move choices."""
        surface.fill((30, 42, 64))
        pygame.draw.ellipse(surface, (74, 102, 120), (700, 150, 360, 120))
        pygame.draw.ellipse(surface, (68, 120, 78), (120, 470, 420, 120))
        enemy_position = self._animated_position((820, 170), is_player=False)
        player_position = self._animated_position((250, 400), is_player=True)
        self._draw_creature(
            surface,
            self.battle.enemy,
            enemy_position,
            (210, 170, 190),
            self.display_enemy_hp,
        )
        self._draw_creature(
            surface,
            self.battle.player,
            player_position,
            (130, 120, 220),
            self.display_player_hp,
        )
        if self.flash_remaining > 0:
            flash = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            flash.fill((255, 255, 255, 45))
            surface.blit(flash, (0, 0))

        message_box = pygame.Rect(40, 40, 700, 100)
        pygame.draw.rect(surface, (20, 24, 36), message_box, border_radius=8)
        pygame.draw.rect(surface, (232, 232, 210), message_box, 3, border_radius=8)
        self._text(surface, self.battle.message, (60, 62), self.font)

        if self.battle.finished:
            self._text(surface, "Press Enter or Space to return", (60, 112), self.small_font)
        else:
            self._draw_menu(surface)

    def _draw_menu(self, surface: pygame.Surface) -> None:
        """Draw the command or move menu at the bottom of the battle screen."""
        menu = pygame.Rect(40, 590, 1120, 110)
        pygame.draw.rect(surface, (20, 24, 36), menu, border_radius=8)
        pygame.draw.rect(surface, (232, 232, 210), menu, 3, border_radius=8)
        if self.menu is BattleMenu.COMMANDS:
            commands = ("Fight", "Pack", "Team", "Run")
            for index, command in enumerate(commands):
                x = menu.x + 35 + (index % 2) * 270
                y = menu.y + 16 + (index // 2) * 40
                color = (255, 230, 100) if index == self.menu_index else (245, 245, 235)
                self._text(surface, f"{'> ' if index == self.menu_index else '  '}{command}", (x, y), self.font, color)
        else:
            if self.menu is BattleMenu.PACK:
                self._text(surface, "Pack", (menu.x + 20, menu.y + 12), self.small_font)
                count = self.profile.inventory.get("Heal Patch", 0)
                item_color = (255, 230, 100) if self.menu_index == 0 else (245, 245, 235)
                self._text(
                    surface,
                    f"> Heal Patch x{count}  (+10 HP)",
                    (menu.x + 35, menu.y + 48),
                    self.font,
                    item_color,
                )
                self._text(surface, "Enter: Use  Esc: Back", (menu.right - 270, menu.bottom - 30), self.small_font)
            elif self.menu is BattleMenu.TEAM:
                self._text(surface, "Team", (menu.x + 20, menu.y + 12), self.small_font)
                for index, creature in enumerate(self.profile.party):
                    marker = "*" if index == self.profile.active_index else " "
                    color = (
                        (255, 230, 100)
                        if index == self.menu_index
                        else (245, 245, 235)
                    )
                    self._text(
                        surface,
                        f"{'> ' if index == self.menu_index else '  '}"
                        f"{marker} {creature.name}  Lv {creature.level}  "
                        f"{creature.current_hp}/{creature.max_hp} HP",
                        (menu.x + 35, menu.y + 44 + index * 30),
                        self.font,
                        color,
                    )
                self._text(surface, "Enter/Escape: Back", (menu.right - 220, menu.bottom - 30), self.small_font)
            else:
                self._text(surface, "Choose a move", (menu.x + 20, menu.y + 12), self.small_font)
                for index, move in enumerate(self.battle.player.moves):
                    x = menu.x + 35 + (index % 2) * 270
                    y = menu.y + 42 + (index // 2) * 32
                    remaining = self.battle.remaining_uses(move)
                    color = (255, 230, 100) if index == self.menu_index else (245, 245, 235)
                    if remaining == 0:
                        color = (110, 110, 120)
                    self._text(
                        surface,
                        f"{'> ' if index == self.menu_index else '  '}"
                        f"{move.name} {remaining}/{move.max_uses}",
                        (x, y),
                        self.font,
                        color,
                    )
                self._text(surface, "Esc: Back", (menu.right - 150, menu.bottom - 30), self.small_font)
        if self.menu_message:
            self._text(surface, self.menu_message, (menu.x + 590, menu.y + 18), self.small_font)

    def _animated_position(
        self,
        position: tuple[int, int],
        *,
        is_player: bool,
    ) -> tuple[int, int]:
        """Return a temporary offset for the built-in placeholder animation."""
        x, y = position
        if self.phase is BattlePhase.PLAYER_ATTACK and is_player:
            progress = min(
                self.animation_elapsed / self.ATTACK_ANIMATION_DURATION,
                1.0,
            )
            x += round(70 * (1.0 - abs(2.0 * progress - 1.0)))
        elif self.phase is BattlePhase.ENEMY_ATTACK and not is_player:
            progress = min(
                self.animation_elapsed / self.ATTACK_ANIMATION_DURATION,
                1.0,
            )
            x -= round(70 * (1.0 - abs(2.0 * progress - 1.0)))
        if self.shake_remaining > 0 and not is_player:
            x += 6 * self.shake_direction
        return x, y

    def _draw_creature(
        self,
        surface: pygame.Surface,
        creature: object,
        position: tuple[int, int],
        color: tuple[int, int, int],
        display_hp: float,
    ) -> None:
        """Draw a placeholder creature and its status panel."""
        x, y = position
        pygame.draw.circle(surface, color, (x, y), 62)
        name = f"{creature.name}  Lv {creature.level}"
        self._text(surface, name, (x - 100, y + 80), self.font)
        bar = pygame.Rect(x - 100, y + 116, 200, 18)
        pygame.draw.rect(surface, (50, 50, 58), bar, border_radius=5)
        ratio = display_hp / creature.max_hp
        pygame.draw.rect(
            surface,
            self._hp_color(ratio),
            (bar.x, bar.y, round(bar.width * ratio), bar.height),
            border_radius=5,
        )
        self._text(
            surface,
            f"{creature.current_hp}/{creature.max_hp} HP",
            (x - 42, y + 142),
            self.small_font,
        )

    @staticmethod
    def _hp_color(ratio: float) -> tuple[int, int, int]:
        """Return a high, mid, or low health color for a normalized value."""
        if ratio > 0.5:
            return (78, 196, 90)
        if ratio > 0.2:
            return (220, 188, 62)
        return (210, 78, 62)

    @staticmethod
    def _text(
        surface: pygame.Surface,
        text: str,
        position: tuple[int, int],
        font: pygame.font.Font,
        color: tuple[int, int, int] = (245, 245, 235),
    ) -> None:
        surface.blit(font.render(text, True, color), position)
