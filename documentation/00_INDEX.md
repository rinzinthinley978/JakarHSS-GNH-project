# Gaki Pelzom (JakarHSS‑GNH‑project) — Technical Documentation

This documentation set explains **every module, class, and function** in the
`JakarHSS-GNH-project` repository (branch `main`), including *why* each piece
exists, *which libraries* it depends on, and *how* the pieces talk to one
another at runtime.

The project itself is a fullscreen Pygame "policy simulation" game: the
player picks a Bhutanese district on a map, then plays 15 turns of decision
scenarios that move four visible "pillars" (Economy, Environment, Culture,
Governance) and five hidden stats (Social Unrest, Ecological Stress,
Corruption Index, Foreign Influence, Public Trust). The code is organized as
one entry-point script (`main.py`) plus a `game_func` package containing one
class per concern (data, fonts, map, UI panel, scene rendering, game state,
scenario/crisis selection, loading screen, main menu).

## How to read this documentation

Because the codebase mixes several distinct concerns (persistence & display
scaling, geospatial map processing, simulation/state logic, and Pygame
rendering), the docs are split into files that group *related* components
together, so each file can be read start‑to‑finish without needing to jump
around:

| File                                                                     | Covers                                                                                                                                                                                                   | Why grouped together                                                                                                                                                                              |
| ------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`01_ARCHITECTURE_AND_ENTRYPOINT.md`](01_ARCHITECTURE_AND_ENTRYPOINT.md) | `main.py`, overall architecture, the state machine, the game loop                                                                                                                                        | This is the "conductor" that owns every other module — best understood first, as a map of how everything connects                                                                                 |
| [`02_DATA_AND_PERSISTENCE.md`](02_DATA_AND_PERSISTENCE.md)               | `game_func/data_loader.py` (`DataLoader`), the JSON data files (`data/*.json`)                                                                                                                           | All persistence, display-scaling, and asset-loading responsibilities live in one class; the JSON schemas it reads/writes are documented alongside it                                              |
| [`03_MAP_AND_GEOSPATIAL.md`](03_MAP_AND_GEOSPATIAL.md)                   | `game_func/districts_process.py` (`DistProc`), `game_func/district_loader.py` (`MapScreen`)                                                                                                              | Both are dedicated to turning GeoJSON district boundaries into clickable on-screen shapes — a single geospatial pipeline split into "process" and "present" halves                                |
| [`04_SIMULATION_ENGINE.md`](04_SIMULATION_ENGINE.md)                     | `game_func/game_state.py` (`GameState`), `game_func/scenario_engine.py` (`ScenarioEngine`), `game_func/crisis_engine.py` (`CrisesEngine`)                                                                | These three classes together form the game's simulation core: state storage, decay math, and content selection (scenarios/crises)                                                                 |
| [`05_UI_AND_RENDERING.md`](05_UI_AND_RENDERING.md)                       | `game_func/ui_panel.py` (`Panel`), `game_func/game_scene.py` (`GameScene`), `game_func/main_menu.py` (`MainMenu`), `game_func/loading.py` (`loadingScreen`), `game_func/font_manager.py` (`FontManager`) | Every screen the player looks at (menu, loading bar, district sidebar, decision scene, end-of-game report) is a thin Pygame drawing layer built on the shared `FontManager`                       |
| [`06_LIBRARIES_AND_DEPENDENCIES.md`](06_LIBRARIES_AND_DEPENDENCIES.md)   | `requirements.txt` and every third-party/standard library import used anywhere in the project                                                                                                            | A single reference explaining *why* each library (pygame, shapely, geojson, matplotlib, numpy, plus stdlib `json`/`random`/`copy`/`os`/`sys`/`time`) is needed and exactly which functions use it |

## Quick project map

```
main.py                          # game loop + finite-state machine (Loading → Menu → Map → Game Scene → End Screen)
game_func/
├── data_loader.py    → DataLoader        # JSON I/O, display scaling, assets, audio
├── font_manager.py   → FontManager       # cached font rendering + word-wrap
├── loading.py        → loadingScreen     # splash/progress-bar screen
├── main_menu.py       → MainMenu         # title screen + Start/Reset/Quit buttons
├── districts_process.py → DistProc       # GeoJSON → screen-space polygons
├── district_loader.py  → MapScreen       # draws + hit-tests the district map
├── ui_panel.py         → Panel           # district sidebar + BEGIN button
├── game_state.py       → GameState       # pillars, hidden stats, decay, history
├── scenario_engine.py  → ScenarioEngine  # picks non-repeating decision scenarios
├── crisis_engine.py    → CrisesEngine    # detects/locks threshold-triggered crises
└── game_scene.py       → GameScene       # renders the turn loop + end-game report
data/
├── game_data.json           # live save file (district pillars/hidden stats)
├── default_data.json        # factory-reset values for all districts
├── decisions.json           # scenario definitions (id, options, effects, advisors)
├── crises.json              # crisis definitions (trigger thresholds, options)
└── bhutan_districts.geojson # district polygon boundaries
```

Read the files in the order listed in the table above for the smoothest
narrative flow — start with the architecture overview, then persistence, then
the map pipeline, then the simulation engine, then rendering, and finish with
the library reference.
