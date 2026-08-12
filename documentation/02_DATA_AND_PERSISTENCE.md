# 2. Data & Persistence — `game_func/data_loader.py`

## Purpose of this module

`DataLoader` (class in `game_func/data_loader.py`) is the project's "god
object" for anything that is **shared infrastructure** rather than
game-specific logic:

- Pygame **window/display setup**, including a virtual-resolution scaling
  system so the game looks correct on any monitor size.
- **Audio/asset loading** (background music, click SFX, icon, cursor).
- **JSON persistence** — loading `data/game_data.json` into memory, saving a
  finished run's stats back to disk, and resetting all districts to factory
  defaults from `data/default_data.json`.
- Small utility methods (`show_fps`, coordinate conversion) used by other
  modules.

It is constructed once in `main.py` and the same instance is threaded through
every other manager class, so there is exactly one Pygame `screen` surface
and one loaded copy of the district JSON data for the whole program.

## Why a virtual-resolution system?

The game always launches `FULLSCREEN | RESIZABLE` at the user's *actual*
monitor resolution (`pygame.display.Info()`), but all layout math elsewhere
in the codebase (map polygon coordinates, UI panel positions, scenario
option boxes) is written against a **fixed virtual canvas of 1366×768**
(16:9). `DataLoader` computes a uniform `scale` factor and centering
`offset_x`/`offset_y` so that this fixed-size virtual layout is scaled up (or
letterboxed) to fit any real screen without distorting the aspect ratio —
similar to how many 2D games handle multi-resolution support. This is why
`DistProc` ([03_MAP_AND_GEOSPATIAL.md](03_MAP_AND_GEOSPATIAL.md)) always projects geography into the
1366×768 virtual space rather than the real screen size.

> **Note:** in the actual game loop today, most screens (`GameScene`,
> `Panel`, `MapScreen`) draw directly onto `data_loader.screen` at native
> resolution using `data_loader.WIDTH`/`HEIGHT`, rather than onto
> `virtual_surface` + `render_frame()`. The virtual-surface/scale machinery
> is fully implemented and used by `MainMenu` (via
> `get_virtual_mouse_pos()`) and is available for any screen that wants
> resolution-independent rendering, but not every screen currently opts in.

## `class DataLoader`

### `__init__(self)`

Responsibilities, in the order they run:

1. **Audio & core image loading**, wrapped in a single `try/except` so a
   missing asset file doesn't crash the whole game — it just prints a
   warning (`"Missing assets found: ..."`) and leaves the game playable
   without that asset:
   - `pygame.mixer.init()` — starts the audio subsystem (called again here
     even though `main.py` already calls it once; harmless/idempotent).
   - `pygame.mixer.music.load("assets/sounds/bgm.wav")` — queues the
     background music track (played later by `main.py`).
   - `pygame.image.load('assets/ui/main_menu.png')` — loaded here but not
     actually used elsewhere as `self.main_menu`; `MainMenu` loads its own
     background image independently.
   - `pygame.image.load("assets/ui/icon.png")` → `self.game_icon`, used by
     `main.py` for `pygame.display.set_icon`.
   - `pygame.mixer.Sound('assets/sounds/click.wav')` → `self.click_sound`,
     volume set to 0.5. (Used by `MainMenu` if a click sound is wired in.)

2. **Virtual canvas + real display setup:**
   ```python
   self.VIRTUAL_WIDTH = 1366
   self.VIRTUAL_HEIGHT = 768
   self.virtual_surface = pygame.Surface((self.VIRTUAL_WIDTH, self.VIRTUAL_HEIGHT))

   display_info = pygame.display.Info()
   self.WIDTH = display_info.current_w
   self.HEIGHT = display_info.current_h

   self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), pygame.FULLSCREEN | pygame.RESIZABLE)
   ```
   `pygame.display.Info()` queries the OS for the current desktop
   resolution *before* a window exists, so the game can open a fullscreen
   window that exactly matches the user's monitor. `FULLSCREEN |
   RESIZABLE` is combined so the window fills the screen but can still
   respond to resolution/display changes.

3. **Scale-factor bookkeeping** — `self.scale`, `scaled_w`, `scaled_h`,
   `offset_x`, `offset_y` are initialized then immediately computed via
   `self.recalculate_scale()` (see below).

4. **Interaction/timing state:** `selected_district`, `hovered` (both start
   `None`), `mousePos` (initial mouse position), `frames = 60` (target
   FPS), `clock = pygame.time.Clock()`.

5. **Custom cursor:** loads `assets/ui/mouse_icon.png`, scales it to 32×32,
   and wraps it in a `pygame.cursors.Cursor((0, 0), mouse_sprite)` — the
   `(0, 0)` hot-spot means the cursor's *top-left* pixel is the click point.
   Falls back to `pygame.SYSTEM_CURSOR_ARROW` if the asset is missing.

6. **District data:** `self.data = {}` then `self.reload_data()` to
   populate it from `data/game_data.json` immediately, so the map/sidebar
   have data as soon as the Menu is reached.

### `recalculate_scale(self)`

```python
scale_x = self.WIDTH / self.VIRTUAL_WIDTH
scale_y = self.HEIGHT / self.VIRTUAL_HEIGHT
self.scale = min(scale_x, scale_y)
self.scaled_w = int(self.VIRTUAL_WIDTH * self.scale)
self.scaled_h = int(self.VIRTUAL_HEIGHT * self.scale)
self.offset_x = (self.WIDTH - self.scaled_w) // 2
self.offset_y = (self.HEIGHT - self.scaled_h) // 2
```

Takes `min(scale_x, scale_y)` rather than stretching each axis
independently — this is the standard technique for **uniform (aspect-ratio
preserving) scaling with letterboxing**: whichever axis is the tighter
constraint determines the scale, and the other axis ends up with unused
space, which `offset_x`/`offset_y` center. This method can be re-invoked if
the window is resized (the window was opened `RESIZABLE`).

### `get_virtual_mouse_pos(self)`

```python
raw_x, raw_y = pygame.mouse.get_pos()
virt_x = (raw_x - self.offset_x) / self.scale
virt_y = (raw_y - self.offset_y) / self.scale
virt_x = max(0, min(self.VIRTUAL_WIDTH, virt_x))
virt_y = max(0, min(self.VIRTUAL_HEIGHT, virt_y))
return int(virt_x), int(virt_y)
```

Converts a raw screen-space mouse coordinate into virtual-canvas coordinates
by inverting the scale/offset transform from `recalculate_scale`, then
clamps the result inside the canvas bounds (so a mouse position just outside
the letterboxed area doesn't register as an out-of-range virtual coordinate).
`MainMenu.get_mouse_pos()` calls this so its buttons — which are laid out in
virtual-canvas coordinates — hit-test correctly regardless of real window
size.

### `render_frame(self)`

```python
self.screen.fill((0, 0, 0))
scaled_surface = pygame.transform.smoothscale(self.virtual_surface, (self.scaled_w, self.scaled_h))
self.screen.blit(scaled_surface, (self.offset_x, self.offset_y))
```

Fills the real screen black (the letterbox bars), smooth-scales whatever was
drawn onto `virtual_surface` up to the computed `scaled_w`/`scaled_h`, and
blits it centered. `smoothscale` (rather than plain `scale`) is used because
it applies filtering, avoiding the blocky/aliased look of nearest-neighbor
scaling when the virtual canvas is enlarged. This method exists for any
screen that draws onto `virtual_surface`; see the note above about which
screens currently do so.

### `show_fps(self, enabled)`

```python
def show_fps(self, enabled):
    if not enabled:
        return
    font = pygame.font.SysFont("Arial", 30)
    frames_per_second = str(int(self.clock.get_fps()))
    fps_rendered = font.render(frames_per_second, True, (255, 0, 0))
    self.screen.blit(fps_rendered, (10, 10))
```

A simple debug overlay: reads the rolling FPS estimate from
`self.clock.get_fps()` and draws it top-left in red. It early-returns if
`enabled` is falsy — and `main.py` currently calls `show_fps(0)`, so this is
effectively disabled in the shipped build but easy to re-enable by changing
that one call site.

### `get_district_data(self)`

```python
if not self.selected_district:
    print("Warning: No district selected.")
    return None
districts = self.data.get("districts", {})
if self.selected_district in districts:
    return districts[self.selected_district]
target_name = str(self.selected_district).strip().lower()
for key, data in districts.items():
    if str(key).strip().lower() == target_name:
        return data
print(f"Warning: Received empty district data for '{self.selected_district}'. Available keys: {list(districts.keys())}")
return None
```

Looks up the currently-selected district's record inside the loaded
`game_data.json`. It tries an **exact key match first** (fast path), and
falls back to a **case/whitespace-insensitive scan** of all district keys —
defensive coding against the map's district names (sourced from the GeoJSON
`shapeName` property, see [03_MAP_AND_GEOSPATIAL.md](03_MAP_AND_GEOSPATIAL.md)) not matching the JSON
keys byte-for-byte (e.g., trailing space or different capitalization from
two independently-authored data sources). If no match is found at all, it
prints the available keys to aid debugging and returns `None`, which callers
(`main.py`'s "begin" handler, `Panel._rebuild_panel_cache`) are written to
handle gracefully.

### `reload_data(self)`

```python
try:
    with open("data/game_data.json", "r") as file_handle:
        self.data = json.load(file_handle)
except Exception as reload_error:
    print(f"Error loading game_data.json: {reload_error}")
    self.data = {"districts": {}}
```

Reads the live save file from disk into `self.data`. Any failure (missing
file, malformed JSON) is caught and replaced with an empty-but-valid
structure `{"districts": {}}` so the rest of the game doesn't crash on a
`KeyError`/`AttributeError` — it will simply show no districts. Called at
startup, after a factory reset, and at the start of every new run
(`reset_game_session()` in `main.py`) to guarantee freshly-written data is
picked up.

### `save_district_data(self, district_name, final_state)`

```python
with open("data/game_data.json", "r") as file_handle:
    full_data = json.load(file_handle)
target_key = None
if district_name in full_data.get("districts", {}):
    target_key = district_name
else:
    for key in full_data.get("districts", {}):
        if key.strip().lower() == str(district_name).strip().lower():
            target_key = key
            break
if target_key:
    full_data["districts"][target_key]["starting_gnh"] = final_state.get("starting_gnh", 50)
    full_data["districts"][target_key]["hidden_vars"] = final_state.get("hidden_vars", {})
    with open("data/game_data.json", "w") as file_handle:
        json.dump(full_data, file_handle, indent=4)
    self.reload_data()
    print(f"Saved progress for {district_name}")
else:
    print(f"District {district_name} not found.")
```

Persists a completed run's final pillar values (`starting_gnh` — reused as
the field name so next time this same district is played, its *ending*
values become the *starting* values, implementing the README's "Persistent
World" feature) and `hidden_vars` back into `game_data.json`. It:

1. Re-reads the file fresh from disk (rather than trusting in-memory
   `self.data`) to avoid clobbering any other changes that may have been
   written to the file since it was last loaded.
2. Uses the same exact-then-case-insensitive key-matching strategy as
   `get_district_data` for consistency.
3. Overwrites only the two relevant fields for that one district, leaving
   `region`, `population`, `description`, etc. untouched.
4. Writes the whole file back with `indent=4` for human-readable diffing if
   the JSON is inspected/edited manually.
5. Calls `self.reload_data()` immediately after saving so `self.data` is
   back in sync with disk.

Called exactly once per run, from `main.py`, the first frame after entering
`'End Screen'`.

### `reset_all_district_data(self)`

```python
with open("data/default_data.json", "r") as default_file:
    default_data = json.load(default_file)
with open("data/game_data.json", "w") as file_handle:
    json.dump(default_data, file_handle, indent=4)
self.reload_data()
print("Successfully reset all district data.")
```

Implements the main menu's "Reset Data" button: copies the entire contents of
the read-only `default_data.json` (factory values for all 20 districts) over
the top of the live `game_data.json`, effectively undoing all campaign
progress. Called from `main.py`'s Menu-state transition block when
`menu_action == "reset"`.

## The JSON data files (`data/`)

These files are the "content" half of the project — everything data-driven
that a designer could edit without touching Python.

### `data/game_data.json` — live save file

Structure:
```json
{
  "districts": {
    "<District Name>": {
      "region": "Central",
      "population": 17800,
      "description": "...",
      "starting_gnh": { "economy": 40, "environment": 65, "culture": 75, "governance": 50 },
      "hidden_vars": { "social_unrest": 25, "ecological_stress": 40, "corruption_index": 20, "foreign_influence": 30, "public_trust": 70 }
    },
    "...": { }
  }
}
```
`starting_gnh` (despite the name, it holds the four *visible pillars*, not
just GNH) and `hidden_vars` are read by `GameState.receive_data` when a run
begins, and overwritten by `DataLoader.save_district_data` when a run ends —
so this file is both the "starting point" and "save slot" for each district
simultaneously, which is how the "your progress carries into the next
playthrough" feature works.

### `data/default_data.json` — factory reset backup

Same shape as `game_data.json`, containing the original hand-authored
starting values for all 20 districts. Never written to by the game — only
read from, by `reset_all_district_data`.

### `data/decisions.json` — scenario library

```json
{
  "decisions": [
    {
      "id": "internet_village_expansion",
      "title": "Internet for Remote Villages",
      "category": "governance",
      "phase": "early",
      "description": "...",
      "prerequisites": {
        "min_turn": 0, "max_turn": 5,
        "forbidden_flags": [], "required_flags": []
      },
      "options": [
        {
          "text": "Approve fiber optic expansion immediately",
          "effects": {
            "pillars": { "economy": 12, "environment": -8, "culture": -6, "governance": 3 },
            "hidden": { "social_unrest": 3, "ecological_stress": 8, "corruption_index": 2, "foreign_influence": 8, "public_trust": -4 }
          },
          "set_flags": ["fiber_optic_internet"],
          "remove_flags": [],
          "delayed": [
            { "turns": 2, "effects": { "pillars": { "culture": -4 }, "hidden": { "foreign_influence": 6 } },
              "message": "Foreign streaming content erodes local storytelling traditions." }
          ],
          "advisors": {
            "economist": "Connectivity will spark entrepreneurship.",
            "ranger": "Trenches will scar pristine habitats.",
            "monk": "Real connection comes from within, not wires."
          }
        }
      ]
    }
  ]
}
```

Consumed entirely by `ScenarioEngine` (loaded once at startup) and rendered
by `GameScene.draw_scenario`. Key fields and who reads them:

| Field | Read by | Purpose |
|---|---|---|
| `id` | `ScenarioEngine.filter_deck` / `GameState.played_scenarios` | Uniquely identifies a scenario so it is never shown twice in a run. |
| `prerequisites.min_turn` / `max_turn` | `ScenarioEngine.filter_deck` | Restricts *which turn range* a scenario can appear in. |
| `prerequisites.required_flags` / `forbidden_flags` | `ScenarioEngine.filter_deck` | Gate scenarios behind (or away from) previously-set flags — see [04_SIMULATION_ENGINE.md](04_SIMULATION_ENGINE.md). |
| `title`, `description` | `GameScene.draw_scenario` | Displayed text. |
| `options[].text` | `GameScene.draw_scenario` | Button label for each of the (usually 2–3) choices. |
| `options[].effects.pillars` / `.hidden` | `GameState.apply_choice` | Immediate stat deltas applied when this option is chosen. |
| `options[].set_flags` / `remove_flags` | `GameState.apply_choice` | Mutates the flag set (top-level, *not* nested under `effects` — an important quirk documented in `game_state.py`'s comments). |
| `options[].delayed` | `main.construct_feedback_message` | Currently used only to source a nicer ghost-feedback message; note the delayed effect itself is **not** separately re-applied by any scheduler in the current codebase — only its `message` string is surfaced. |
| `options[].advisors.{economist,ranger,monk}` | `GameScene.draw_scenario` | Hover-tooltip text shown per advisor persona. |

### `data/crises.json` — crisis library

```json
{
  "crises": [
    {
      "id": "economic_collapse",
      "flag": "eco_collapse",
      "title": "Economic Collapse",
      "description": "...",
      "trigger": { "type": "pillar", "conditions": { "economy": { "max": 25 } } },
      "options": [ { "text": "...", "effects": { "pillars": {...}, "hidden": {...} }, "advisors": {...} } ]
    }
  ]
}
```

Consumed by `CrisesEngine`. `trigger.type` is one of `"pillar"`, `"hidden"`,
or `"combined"`, selecting which stat dictionary `conditions` is checked
against; each condition entry may specify a `"min"` and/or `"max"` numeric
threshold that the current stat value must satisfy. Full evaluation logic is
documented in [04_SIMULATION_ENGINE.md](04_SIMULATION_ENGINE.md).

### `data/bhutan_districts.geojson` — map geometry

Standard [GeoJSON](https://geojson.org/) `FeatureCollection`; each feature's
`geometry` is a `Polygon`/`MultiPolygon` of longitude/latitude coordinates,
and `properties.shapeName` supplies the district's display name. Consumed
exclusively by `DistProc` — see [03_MAP_AND_GEOSPATIAL.md](03_MAP_AND_GEOSPATIAL.md).
