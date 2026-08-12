# 1. Architecture & Entry Point — `main.py`

## Purpose

`main.py` is the single executable script that starts the game. It does four
jobs, in order:

1. **Boots Pygame** and constructs one instance of every manager class the
   game needs (data, fonts, screens, engines).
2. **Owns the finite‑state machine** (`current_state`) that decides which
   screen is active: `"Loading" → "Menu" → "Map" → "Game Scene" → "End Screen"`
   (with `"Game Scene"/"End Screen" → "Map"` on `ESC`).
3. **Runs the game loop** — the classic Pygame pattern of *handle events →
   update logic → draw → flip* repeated 60 times a second.
4. **Bridges modules together** — e.g., taking the dictionary a player's
   click returns from `GameScene` and feeding it into `GameState`, or taking
   `GameState`'s hidden stats and feeding them into `CrisesEngine`.

Because every other module in this project is a self-contained class with no
knowledge of the others, `main.py` is the only place that needs to be read to
understand *how the pieces fit together end-to-end*. The per-class detail is
in the other documentation files; this file explains the wiring.

## Why this architecture?

The project deliberately avoids a generic "game engine" or scene-manager
framework. Instead it uses:

- **Composition over inheritance** — `main.py` constructs one instance of
  each class and passes shared dependencies (`data_loader`, fonts) into each
  constructor. There is no base `Scene` class; every screen module simply
  exposes `draw(...)`/`handle_events(...)`-style methods that `main.py` calls
  conditionally based on `current_state`.
- **A single flat state variable (`current_state`)** rather than a stack or
  scene graph — appropriate because the game only ever has one screen active
  at a time and the flow between screens is linear/cyclical (Menu → Map →
  Game Scene → End Screen → Map …).
- **Deferred effect application via "pending" variables** — see
  [Ghost-feedback / pending-choice flow](#ghost-feedback--pending-choice-flow)
  below — so that the *visual* consequence of a choice (a 2-second narrative
  message) can play out before the *numerical* consequence is committed to
  `GameState`.

## Module-level setup

```python
pygame.init()
pygame.mixer.init()

data_loader = DataLoader()
heading_font = FontManager('assets/ui/pixel_heading.ttf')
body_font = FontManager('assets/ui/pixel_body.ttf')

loading_screen = loadingScreen(data_loader, heading_font)
info_panel = Panel(data_loader, heading_font, body_font)
game_scene = GameScene(data_loader, info_panel, heading_font, body_font)
district_processor = DistProc(data_loader)
map_screen = MapScreen(data_loader, district_processor, heading_font)
game_state = GameState(data_loader)
scenario_engine = ScenarioEngine()
crisis_engine = CrisesEngine()
main_menu = MainMenu(data_loader, heading_font, body_font)
```

Every manager receives `data_loader` (or an object built from it) because
`DataLoader` is the single source of truth for the Pygame `screen` surface,
window dimensions, virtual-canvas scaling, and loaded JSON district data —
see [02_DATA_AND_PERSISTENCE.md](02_DATA_AND_PERSISTENCE.md). Passing the same instance everywhere avoids
duplicating window/asset state.

After construction, `main.py`:

- Starts looping background music: `pygame.mixer.music.play(-1)` (loop
  forever) at 50% volume.
- Sets the window icon/title/cursor from data already loaded by
  `DataLoader.__init__`.

## Global game-state variables

```python
running = True
current_state = "Loading"
hover_index = None
pending_choice = None
pending_scenario = None
pending_was_crisis = False
current_scenario = None
is_current_crisis = False
game_saved = False
menu_action = None
```

| Variable | Type | Meaning |
|---|---|---|
| `running` | `bool` | Master loop flag; set to `False` on window-close or Quit-menu click to end the program. |
| `current_state` | `str` | Which screen is active: `"Loading"`, `"Menu"`, `"Map"`, `"Game Scene"`, `"End Screen"`. |
| `hover_index` | `int \| None` | Index of the scenario option currently hovered (used to show advisor hints). Recomputed every frame while in `"Game Scene"`. |
| `pending_choice` | `dict \| None` | The chosen option's effect dictionary, held until the 2‑second "ghost" narrative animation finishes. |
| `pending_scenario` | `dict \| None` | The scenario/crisis dict that was active when the choice was made (needed afterwards to mark it played). |
| `pending_was_crisis` | `bool` | Whether `pending_scenario` was a crisis (routes to `crisis_engine.resolve_crisis()`) or a normal scenario (routes to `game_state.update_scenario_details()` + `scenario_engine.clear_lock()`). |
| `current_scenario` | `dict \| None` | The scenario or crisis currently being displayed to the player. |
| `is_current_crisis` | `bool` | Whether `current_scenario` came from `CrisesEngine` rather than `ScenarioEngine`. |
| `game_saved` | `bool` | Guards against writing the save file more than once per End Screen visit. |
| `menu_action` | `str \| None` | The action returned by `MainMenu.handle_events` (`"start"`, `"reset"`, `"quit"`) — applied on the next iteration's state-transition block. |

## Helper functions defined in `main.py`

### `reset_game_session()`

```python
def reset_game_session():
    global current_scenario, pending_choice, pending_scenario, game_saved, is_current_crisis, pending_was_crisis
    data_loader.reload_data()
    game_state.reset()
    game_scene.reset()
    scenario_engine.clear_lock()
    crisis_engine.reset()
    data_loader.selected_district = None
    current_scenario = None
    pending_choice = None
    pending_scenario = None
    pending_was_crisis = False
    game_saved = False
    is_current_crisis = False
```

**Why it exists:** every manager class keeps its own mutable per-run state
(`GameState` tracks pillars/turn, `GameScene` tracks counters/ghost timers,
`ScenarioEngine`/`CrisesEngine` track locks and cooldowns). Rather than
re-instantiating all of these objects (which would also reload fonts, images,
and JSON unnecessarily), `reset_game_session()` calls each object's own
`reset()`/`clear_lock()` method and clears `main.py`'s own globals. This is
called whenever the player leaves a completed or abandoned run — pressing
`ESC` from `"Game Scene"`/`"End Screen"`, or returning to the map after
finishing the End Screen.

`data_loader.reload_data()` is called first so that the freshly-saved
`game_data.json` (written just before entering the End Screen) is re-read
into memory, ensuring the map/sidebar shows up-to-date district stats for the
next run.

### `construct_feedback_message(choice_effect)`

```python
def construct_feedback_message(choice_effect):
    effects = choice_effect.get('effects', choice_effect)
    delayed = choice_effect.get('delayed', [])

    if delayed and len(delayed) > 0 and delayed[0].get('message'):
        return delayed[0]['message']

    pillars = effects.get('pillars', {})
    positive = [name.capitalize() for name, magnitude in pillars.items() if magnitude > 0]
    negative = [name.capitalize() for name, magnitude in pillars.items() if magnitude < 0]

    parts = []
    if positive:
        parts.append(f"{', '.join(positive)} flourishes")
    if negative:
        parts.append(f"{', '.join(negative)} suffers")

    return '. '.join(parts) + '.' if parts else "The consequences of your decision will unfold in time..."
```

**Purpose:** turns a raw JSON "choice" object from `decisions.json` /
`crises.json` into a short, human-readable sentence to display during the
"ghost" narrative phase (see below), without requiring every single choice in
the JSON data to hand-author a message string.

**Logic, step by step:**
1. `choice_effect.get('effects', choice_effect)` — some choice dicts nest
   their pillar/hidden deltas under an `"effects"` key; this line falls back
   to treating the dict itself as the effects if that key is absent, so the
   function is tolerant of both shapes.
2. If the choice has a `"delayed"` list (a future consequence that fires a
   few turns later) *and* the first delayed entry supplies its own
   `"message"`, that authored message is preferred — it's usually more
   narratively interesting than an auto-generated one (e.g., "Foreign
   streaming content erodes local storytelling traditions.").
3. Otherwise, it inspects `effects['pillars']` (a `{pillar_name: delta}`
   dict), splits pillar names into "positive" (delta > 0) and "negative"
   (delta < 0) buckets, and builds a sentence like `"Economy, Governance
   flourishes. Culture suffers."`
4. If there are no pillar deltas at all, it falls back to a generic line so
   the UI is never left blank.

This is a pure function (no side effects) — it only reads `choice_effect` and
returns a string, making it easy to reason about and test independently of
Pygame.

## The game loop

The loop body has four clearly separated sections, executed every frame:

### a) Event handling

```python
for event in pygame.event.get():
    if event.type == pygame.QUIT:
        running = False
    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
        if current_state in ('Game Scene', 'End Screen'):
            reset_game_session()
            current_state = 'Map'
    if current_state == "Menu": ...
    elif current_state == 'Map': ...
    elif current_state == 'Game Scene': ...
    elif current_state == 'End Screen': ...
```

Pygame's event queue is drained once per frame. `ESC` is handled globally
(works from any sub-branch) because it is the game's universal "go back"
shortcut. Every other event is routed based on `current_state` to the
relevant manager's own `handle_events`/`check_click` method, keeping input
logic co-located with the screen that owns it rather than duplicated in
`main.py`.

**Map state clicks** are the most involved: a left-click first asks
`info_panel.handle_events(event)` whether it hit the "back" or "begin"
button; only if neither was hit does it fall through to
`map_screen.check_click()` (district selection). This ordering matters — the
sidebar UI sits visually on top of the map, so UI hits must be checked first
or a click meant for the BEGIN button could instead be misread as a map
click. When "begin" is pressed:

```python
district_data = data_loader.get_district_data()
if district_data:
    game_state.receive_data(district_data)
    game_scene.reset()
    crisis = crisis_engine.check_crises(game_state)
    if crisis:
        current_scenario = crisis
        is_current_crisis = True
    else:
        current_scenario = scenario_engine.filter_deck(
            game_state.turn, game_state.played_scenarios, game_state.flags
        )
        is_current_crisis = False
    current_state = 'Game Scene'
```

Note that **crises are always checked before scenarios** for the very first
event of a run too — if a district's starting hidden stats already exceed a
crisis threshold (e.g., corruption already high from a previous playthrough),
the player is immediately confronted with that crisis rather than a routine
policy scenario. This models "you're inheriting problems from your
predecessor."

**Game Scene clicks** call `game_scene.handle_choice(event, mousePos)`; if it
returns a non-`None` effect dict, that becomes `pending_choice` (see next
section) rather than being applied immediately.

**End Screen clicks** only check for a click on `game_scene.back_rect` (the
back-arrow button) to trigger `reset_game_session()` and return to `'Map'`.

### b) Ghost-feedback / pending-choice flow

```python
if pending_choice and not game_scene.ghost_active:
    game_state.apply_choice(pending_choice)
    if isinstance(pending_scenario, dict) and 'id' in pending_scenario:
        if pending_was_crisis:
            crisis_engine.resolve_crisis()
        else:
            game_state.update_scenario_details(pending_scenario['id'])
            scenario_engine.clear_lock()
    pending_choice = None
    pending_scenario = None
    pending_was_crisis = False

    crisis = crisis_engine.check_crises(game_state)
    if crisis:
        current_scenario = crisis
        is_current_crisis = True
    else:
        current_scenario = scenario_engine.filter_deck(
            game_state.turn, game_state.played_scenarios, game_state.flags
        )
        is_current_crisis = False
```

This is the heart of the turn loop's "why does it feel like the story pauses
before stats change" design (the README calls this **Ghost Feedback**):

1. When the player clicks an option, `GameScene.handle_choice` immediately
   starts a 2‑second "ghost" animation (`game_scene.ghost_active = True`,
   see [05_UI_AND_RENDERING.md](05_UI_AND_RENDERING.md)) showing the narrative message from
   `construct_feedback_message`, but the numeric effect is *stashed* in
   `pending_choice` rather than applied.
2. Every subsequent frame, `main.py` checks `if pending_choice and not
   game_scene.ghost_active` — i.e., "is there a decision waiting, and has the
   2-second animation now finished?" Only then does it call
   `game_state.apply_choice(pending_choice)`, which performs the actual
   pillar/hidden-stat math (see [04_SIMULATION_ENGINE.md](04_SIMULATION_ENGINE.md)).
3. After applying, it records the scenario as played (or resolves the
   crisis), clears the pending variables, and immediately re-evaluates
   whether a *new* crisis has been triggered by the just-applied stat
   changes — creating the crisis-interrupt gameplay loop described in the
   README ("Corruption > 60 triggers urgent crises").

This deferred-application pattern is why `pending_choice` /
`pending_scenario` / `pending_was_crisis` exist as separate globals instead
of applying effects synchronously inside the event-handling block.

### c) End-of-game checks

```python
if current_state == 'Game Scene' and game_state.turn >= 15:
    current_state = 'End Screen'

if current_state == 'End Screen' and not game_saved:
    final_state = game_state.get_final_state()
    data_loader.save_district_data(data_loader.selected_district, final_state)
    game_saved = True
```

Once `GameState.turn` reaches 15 (the `apply_choice` method increments `turn`
after each non-crisis choice — crises don't consume a turn, by design, so
they're a genuine "interrupt"), the state machine moves to `'End Screen'`.
The very first frame in that state persists the run's final pillar/hidden
values back to `game_data.json` via `DataLoader.save_district_data`, guarded
by `game_saved` so repeated frames don't re-write the file.

### d) State transitions & rendering

```python
if current_state == "Loading":
    loading_screen.do_work(delta_time)
    if loading_screen.loading_finished:
        current_state = "Menu"
elif current_state == "Menu" and menu_action:
    if menu_action == "start": current_state = "Map"
    elif menu_action == "reset": data_loader.reset_all_district_data()
    elif menu_action == "quit": running = False
    menu_action = None
elif current_state == 'Map':
    map_screen.check_hover()
```

then:

```python
data_loader.screen.fill('#fff0f1')
if current_state == "Loading": loading_screen.check_loading()
elif current_state == "Menu": main_menu.draw(data_loader.screen)
elif current_state == 'Map':
    map_screen.draw(data_loader.screen)
    info_panel.draw_panel()
elif current_state == 'Game Scene':
    hover_index = game_scene.handle_hover()
    game_scene.display_info(game_state)
    game_scene.draw_scenario(current_scenario, hover_index)
elif current_state == 'End Screen':
    game_scene.draw_end_screen(game_state)
data_loader.show_fps(0)
pygame.display.flip()
```

Each frame ends by clearing the screen to a background color, delegating to
exactly one drawing routine based on `current_state`, and calling
`pygame.display.flip()` to present the frame. `data_loader.show_fps(0)` is
called with `enabled=0` (i.e., `False`), so in the current build the FPS
counter is permanently disabled — a debugging hook left in place but turned
off (see [02_DATA_AND_PERSISTENCE.md](02_DATA_AND_PERSISTENCE.md) for `show_fps`).

## `pygame.time.Clock` and delta time

```python
delta_time = data_loader.clock.tick(data_loader.frames)
```

`data_loader.clock` is a `pygame.time.Clock()` created in `DataLoader`, and
`data_loader.frames = 60` caps the loop at 60 FPS. `Clock.tick(60)` both
throttles the loop to that rate *and* returns the number of milliseconds
since the previous call, which is stored as `delta_time` and passed into
`loading_screen.do_work(delta_time)` so the loading bar fills at a
frame-rate-independent pace.

## Program exit

```python
pygame.quit()
sys.exit()
```

Standard Pygame teardown once `running` becomes `False`, releasing the
display/audio subsystems before the interpreter exits.
