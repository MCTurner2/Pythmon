# Pythmon

Pythmon is a classic 2D Pokemon-inspired game prototype built with Pygame
and the reusable `two-d-game-engine` package.

The project keeps the engine responsible for the application loop, timing,
input, and rendering lifecycle. Pythmon owns its tile-based world, game
states, creatures, battles, data, and save system.

## Running

Install the reusable engine from its separate project first, then install
Pythmon in editable mode. Both installs must use the same Python environment:

```powershell
cd "$HOME\2D_Game_Engine"
python -m pip install -e .

cd "$HOME\Pythmon"
python -m pip install -e .
```

Then launch the prototype:

```powershell
pythmon
```

On Windows, if the `pythmon` command is not recognized, activate the
project's virtual environment first:

```powershell
cd "$HOME\Pythmon"
.\.venv\Scripts\Activate.ps1
python -m pythmon
```

The module form (`python -m pythmon`) is equivalent to the `pythmon` command
and is usually the most reliable way to launch from a Windows terminal.

## Editing the first map

The prototype world is stored in
`src/pythmon/data/maps/starter_town.txt`. Each character represents one
48-pixel tile:

- `#` is a solid wall.
- `.` is walkable ground.
- `,` is walkable wild-program grass.
- `~` is solid water.
- `P` is the player spawn.
- `N` is an NPC marker.
- `H` is a healing-station marker.

The map loader converts the text into a `GameMap`, while `TileMap` owns
rendering and tile behavior. This keeps the world editable as text now while
leaving room to replace the source with JSON or Tiled data later. Map rows
must remain rectangular.

Walk next to an NPC, face them, and press `E` or `Space` to start a dialogue.
Press the same key to advance the messages. Movement is paused while dialogue
is open. NPC text is currently defined in
`src/pythmon/world/npc.py`.

After talking to Professor Stack, stand next to the NPC while facing them and
press `B` to start the first battle. The outer battle menu uses `Fight`, `Pack`,
`Team`, and `Run`. Use the
arrow keys, including `Left` and `Right`, to select an option and `Enter` or
`Space` to confirm. `Fight` opens the move menu; choose `Esc: Back` or press
`Escape` to return to the outer menu. `Pack` and
`Team` can heal, inspect, and switch party members. `Run` is unavailable in
the current trainer battle. Press `Enter` or `Space` after the battle to
return to the overworld.

Walk through comma-marked grass to encounter wild programs. Each step in
grass has a 20% encounter chance. Wild battles use the same persistent party
and move-use rules as trainer battles, and returning from battle preserves the
overworld position.

Stand next to the yellow `H` Recovery Hub and press `E` or `Space` to restore
the entire party's HP and move uses. The hub does not consume items.

Battle presentation is deliberately separated from battle rules. The
`BattleEffects` hooks in `src/pythmon/states/battle.py` reserve integration
points for attack animations and sound effects without requiring assets yet.
Returning from a battle restores the same overworld state, so the player
remains at the exact location where the battle began.

The current game session also keeps a player profile in memory. Bytebug is
shared between battles, so its HP persists. The `Team` menu displays the
current party, and `Pack` contains three starter Heal Patches that restore
10 HP when Bytebug is injured. This session profile and its persistence format
are intentionally asset-free.

Using a Heal Patch successfully consumes the player's turn. The recovery
message appears in the main battle text box, the opponent then attacks, damage
is reported there, and the menu returns to the outer command menu. An item
that cannot be used does not consume a turn.

Player profiles can be saved and loaded as versioned JSON:

```python
from pathlib import Path

game.save(Path("save/profile.json"))
game.load(Path("save/profile.json"))
```

Save data contains the party, current HP, active creature, moves, and
inventory. Malformed or unsupported save files raise an explicit `ValueError`
instead of silently resetting progress.

At startup, Pythmon automatically loads `save/profile.json` when it exists.
Missing saves start a new profile. Invalid save data is not overwritten; the
game starts a new session and reports the load error the next time the
in-world menu is opened. Callers that use `load()` directly receive the
explicit exception.

Press `Escape` while exploring to open the in-world menu. It provides:

- `Team` — view creature levels and current HP.
- `Pack` — use Heal Patches outside battle.
- `Save` — write the current profile to `save/profile.json`.
- `Resume` — close the menu and return to exploration.

The overworld is paused while this menu is open, and closing it restores the
same map position and facing direction.

The Team screen provides a party list and a creature summary card. Use
`Up`/`Down` to choose a party member and `Enter`/`Space` to make that creature
the active party member. The summary shows a placeholder portrait, HP, level,
attack, defense, and known moves with their current/max uses. Final creature
images can replace the placeholder without changing the party UI.

Battle turns also have explicit presentation pauses: the player's move
resolves first, the enemy response waits briefly, and the result remains on
screen before returning to the overworld. Future animations and sounds can
use these same phases without changing battle rules.

The battle screen currently includes placeholder attack movement, a hit flash,
and a target shake. `BattlePhase` in `src/pythmon/states/battle.py` exposes
the sequence (`READY`, `PLAYER_ATTACK`, `ENEMY_ATTACK`, `RESULT`, and
`COMPLETE`) for replacing these placeholders with final assets later.
Sound callbacks receive event names such as `move:Print` and can be connected
to an audio system when sound assets are added. Move effects now play before
damage is committed, including on the move that defeats a creature, and health
bars drain smoothly to their new values during the attack animation.
Health bars use green above 50%, yellow above 20%, and red at or below 20%.
Each move now has limited uses per battle. The move menu displays remaining
uses as `current/max`; depleted moves are dimmed and selecting one does not
consume a turn. Player move depletion is stored in the profile and survives
saving/loading. Enemy move usage remains local to each encounter.

The battle Team screen can switch to another non-defeated party member. A
switch consumes the player's turn, sends the new creature into battle, and
allows the opponent to respond. Defeated creatures cannot be selected.
`PlayerProfile.restore_party()` provides an explicit full-party recovery API
for future healing stations or rest locations; it is not called automatically.
