# 6. Libraries & Dependencies — `requirements.txt` and standard library usage

## Purpose of this module

This file is the single reference for every third-party package and standard
library module imported anywhere in the project. It explains *why* each
dependency exists, *which specific features* are used, and *which source files*
import them. If you are setting up a fresh environment or auditing the
project's supply chain, start here.

---

## Third-party packages (`requirements.txt`)

### 🎮 `pygame >= 2.6.0`

**Used by:** every UI/rendering module and `DataLoader`.

Pygame is the project's sole graphics, audio, and windowing framework. Specific
subsystems touched:

- **`pygame.display`** — window creation (`set_mode`, `set_caption`,
  `set_icon`, `flip`), fullscreen/RESIZABLE flags, and `display.Info()` for
  native monitor resolution detection (`DataLoader`).
- **`pygame.Surface`** — the universal image buffer. Every texture, text
glyph, panel background, and Matplotlib graph is ultimately a `Surface`.
  Used for `blit`, `fill`, `set_alpha`, `convert_alpha`, and `SRCALPHA`.
- **`pygame.draw`** — `draw.polygon` for district map rendering
  (`MapScreen`), `draw.rect` for scenario option buttons (`GameScene`).
- **`pygame.font.Font` / `pygame.font.SysFont`** — text rasterisation
  (`FontManager`).
- **`pygame.image.load`** — PNG asset ingestion (menus, buttons, panels,
  cursors, icons). Supports `.convert_alpha()` for transparency.
- **`pygame.mixer`** — audio playback. `pygame.mixer.music` streams the
  background music (`bgm.wav`); `pygame.mixer.Sound` plays one-shot SFX
  (click, success, lock). `Sound.set_volume()` and `music.set_volume()` control
  loudness.
- **`pygame.cursors.Cursor`** — custom mouse cursor from a 32×32 sprite
  (`DataLoader`).
- **`pygame.time.Clock`** — frame-rate throttling and delta-time measurement
  (`DataLoader.clock`, consumed by `loadingScreen.do_work()` and the main
  loop).
- **`pygame.Rect`** — 2D rectangle geometry for hit-testing, clipping, and
  positioning. Ubiquitous.
- **`pygame.event`** — event queue polling (`QUIT`, `MOUSEBUTTONDOWN`,
  `MOUSEBUTTONUP`, `KEYDOWN`).
- **`pygame.mouse`** — position queries (`get_pos`, `get_pressed`).

Pygame 2.6.0 is specified because earlier 2.x versions had subtle behavioural
differences in `smoothscale` and `convert_alpha` that could affect the
letterboxed virtual-surface rendering path.

### 📐 `shapely >= 2.0.6`

**Used by:** `districts_process.py` and `district_loader.py`.

Shapely provides robust 2D geometric operations. The project uses:

- **`shapely.geometry.Polygon`** — constructing screen-space district shapes
  from coordinate lists for point-in-polygon tests.
- **`shapely.geometry.MultiPolygon`** — handling districts whose GeoJSON
  geometry consists of multiple disjoint landmasses.
- **`shapely.geometry.shape`** — converting a raw GeoJSON geometry dict
  (a nested list of coordinates) into a Shapely object in one call.
- **`shapely.geometry.Point`** — temporary point objects created during
  `MapScreen.check_hover()` to test `polygon.contains(point)`.
- **`polygon.bounds`** — read-only property returning `(minx, miny, maxx, maxy)`
  for cheap bounding-box pruning before expensive `contains()` calls.

Shapely 2.0+ is required because the vectorised geometry backend is
significantly faster than the 1.x pure-Python fallback, and the `shape()`
factory is stable in the 2.x API.

### 🗺️ `geojson >= 3.1.0`

**Used by:** `districts_process.py` (indirectly).

The GeoJSON file is actually parsed with the standard `json` module, not the
`geojson` library's object model. However, `geojson` is listed in
`requirements.txt` because the project was prototyped with it and the
dependency was retained. It is **not imported anywhere** in the current
source tree. It can be safely removed from `requirements.txt` unless future
features (e.g., GeoJSON validation, re-projection) need it.

### 📈 `matplotlib >= 3.8.0`

**Used by:** `game_scene.py`.

Matplotlib renders the end-of-game trajectory graph. Specific APIs:

- **`matplotlib.use('Agg')`** — forces the non-interactive Agg backend so
  that `pyplot` never tries to open a GUI window. This must be called *before*
  importing `pyplot`.
- **`matplotlib.pyplot.subplots`** — creates the figure and axes.
- **`matplotlib.backends.backend_agg.FigureCanvasAgg`** — renders the figure
  to an in-memory RGBA buffer without disk I/O.
- **`FigureCanvasAgg.draw()`** — executes the render pipeline.
- **`FigureCanvasAgg.buffer_rgba()`** — returns the raw pixel buffer.
- **`FigureCanvasAgg.get_width_height()`** — dimensions for Pygame surface
  creation.
- **`plt.close(fig)`** — explicit figure destruction to prevent memory leaks.

The version constraint `>=3.8.0` ensures compatibility with Python 3.12 and
stable Agg buffer access.

### 🔢 `numpy >= 1.24.0`

**Used by:** `game_scene.py`.

NumPy is used for two purposes:

1. **Sound synthesis** in `GameScene.create_sound()`:
   - `np.linspace` — generates evenly spaced time samples.
   - `np.sin` — sine wave oscillator.
   - `np.exp` — exponential decay envelope.
   - `np.vstack` — stereo channel duplication.
   - `np.max`, `np.abs` — normalisation.
   - `.astype(np.int16).tobytes()` — converts the float array to raw audio
     bytes for `pygame.mixer.Sound(buffer=...)`.

2. **Matplotlib compatibility** — Matplotlib 3.8+ uses NumPy arrays
   internally for line data; while the project doesn't call NumPy directly for
   graphing, Matplotlib's Agg backend requires NumPy at import time.

---

## Standard library modules

### `json`

**Used by:** `data_loader.py`, `scenario_engine.py`, `crisis_engine.py`,
`main_menu.py`, `districts_process.py`.

- `json.load()` — reads `game_data.json`, `default_data.json`,
  `decisions.json`, `crises.json`, `bhutan_districts.geojson`,
  `menu_config.json`.
- `json.dump()` — writes updated district data back to `game_data.json` with
  `indent=4` for human readability.

### `random`

**Used by:** `scenario_engine.py`, `crisis_engine.py`, `game_scene.py`.

- `random.choice()` — selects a random qualifying scenario or crisis from a
  filtered list.
- `random.shuffle()` — shuffles scenario options so their on-screen order
  changes every time.
- `random.randint()` — generates fake spinning numbers during pillar counter
  animations.
- `random.sample()` — selects distinct colours from the option button palette.

### `copy`

**Used by:** `game_state.py`.

- `copy.deepcopy()` — creates independent copies of the `pillars` and
  `hidden` dicts before saving them to disk. Without this, the JSON file
  would contain references to mutable objects that could be modified in-place
  later.

### `os`

**Used by:** `main_menu.py`.

- `os.path.exists()` — checks whether a button image path from
  `menu_config.json` actually exists before attempting `pygame.image.load()`.

### `sys`

**Used by:** `main.py`.

- `sys.exit()` — clean interpreter shutdown after `pygame.quit()`.

### `time`

**Used by:** `main.py`.

- `time.sleep(0.5)` — a short pause after Pygame initialisation before the
  game loop starts. This gives the audio subsystem and display server time to
  settle, reducing the chance of a black frame or audio crackle on startup.

---

## Dependency footprint summary

| Package | Runtime critical? | Can be removed if... |
|---|---|---|
| `pygame` | **Yes** | The entire game is built on it. |
| `shapely` | **Yes** | You replace point-in-polygon with a custom raster mask or pre-baked hit regions. |
| `geojson` | No | Not imported; safe to remove unless future geospatial features need it. |
| `matplotlib` | **Yes** | You remove the end-screen graph or replace it with a hand-drawn Pygame chart. |
| `numpy` | **Yes** | You remove generated sound effects and the Matplotlib graph. |

The standard library modules (`json`, `random`, `copy`, `os`, `sys`, `time`)
are all part of Python's built-in distribution and require no installation.

---

## Version pinning rationale

`requirements.txt` uses **minimum versions** (`>=`) rather than exact pins
(`==`). This was chosen because:

- The project targets "Python 3.12.x" and expects users to create a fresh
  virtual environment.
- Pygame, Shapely, Matplotlib, and NumPy maintain backward-compatible APIs
  within major version lines.
- Exact pins would force users to downgrade already-installed packages if they
  share a virtual environment with other projects.

If the project is ever packaged for distribution (e.g., PyInstaller or
Pygame-ce bundling), the build pipeline should generate a `requirements.lock`
with exact hashes to ensure reproducible builds.
