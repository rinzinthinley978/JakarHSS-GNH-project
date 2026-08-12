# 5. UI & Rendering — `game_func/ui_panel.py`, `game_func/game_scene.py`, `game_func/main_menu.py`, `game_func/loading.py`, `game_func/font_manager.py`

## Purpose of these modules

Every pixel the player sees passes through one of these five classes. They
form a thin rendering layer on top of Pygame — no custom engine, no shader
pipeline, just surfaces, blits, and rects. The design philosophy is
**immediate-mode rendering**: every frame, the active screen clears and redraws
itself from scratch. There is no retained scene graph, no dirty-rectangle
optimisation, and no double-buffering beyond what Pygame already provides.

This is appropriate because:
- The game is 2D with low entity counts (≤20 districts, ≤3 buttons, ≤4
  counters).
- Every frame has significant visual change (animated number counters,
  hover states, ghost fade).
- The team is small; a simple "draw everything every frame" loop is easier to
  reason about than a retained UI framework.

---

## `class FontManager` — `game_func/font_manager.py`

### `__init__(self, font_path)`

Stores the path to a `.ttf` file and an empty `_font_cache` dict. The class
is instantiated twice in `main.py`: once for headings (`pixel_heading.ttf`)
and once for body text (`pixel_body.ttf`).

### `_get_font(self, size)`

Lazy-loads and caches `pygame.font.Font` instances by integer size. If the
file fails to load (missing, corrupted, unsupported format), it falls back to
`pygame.font.SysFont("Arial", size)`. This means a missing pixel font doesn't
crash the game — it just looks different.

### `Font(self, text, color, size)`

Renders a single-line string to a Pygame `Surface` with **antialiasing
disabled** (`False`). Pixel fonts are designed for sharp edges; bilinear
filtering would blur them into illegibility.

### `wrap_text(self, text, color, size, max_width, line_spacing=5, align="center")`

The workhorse text renderer for multi-line content (scenario descriptions,
advisor quotes, end-screen grades). It implements a greedy word-wrap:

1. Split the input on spaces.
2. Accumulate words into a test line until `font.size(test_line)` exceeds
   `max_width`.
3. Commit the current line and start a new one with the overflow word.
4. Render each committed line onto a single tall `Surface` with
   `pygame.SRCALPHA`.

Alignment is supported per-line: `"left"`, `"right"`, or `"center"` (default).
This is used extensively by `GameScene` to fit long scenario descriptions into
the top-right quadrant without horizontal overflow.

---

## `class loadingScreen` — `game_func/loading.py`

### `__init__(self, data_loader_instance, font_manager_instance)`

Loads three UI assets:
- `loading_bar_layout.png` — the empty bar frame.
- `loading_bar_progress.png` — the green fill strip.
- `icon.png` — the game logo, scaled to 370×370 for the splash.

If any asset is missing, it constructs solid-colour fallback surfaces so the
loading screen still renders (grey box, green rectangle, grey square). This
is the same defensive pattern used throughout the project.

Positions are calculated as ratios of the real screen width/height
(`data_loader.WIDTH`, `data_loader.HEIGHT`), not the virtual canvas. This is
an exception to the virtual-resolution rule — the loading screen is the very
first thing the player sees, before any district or menu geometry is loaded,
so it uses native pixels to guarantee it fills the monitor.

### `do_work(self, delta_time)`

Advances `self.loading_progress` based on elapsed milliseconds. The target is
`self.work = 1000` arbitrary units over `self.target_duration_ms = 3000`
milliseconds (3 seconds). Because `delta_time` comes from
`data_loader.clock.tick()`, the bar fills at a real-time pace independent of
frame rate.

When progress reaches 1000, `self.loading_finished` becomes `True`, which
`main.py` detects to transition from `"Loading"` to `"Menu"`.

### `check_loading(self)`

Draws the loading screen. The key technique is **clip-area blitting**:

```python
ratio = self.loading_progress / float(self.work)
current_width = int(self.max_bar_width * ratio)
clip_area = pygame.Rect(0, 0, current_width, self.bar_height)
self.screen.blit(self.loading_bar_progress, self.loading_bar_progress_rect, area=clip_area)
```

Instead of scaling the progress image every frame (expensive and blurry), it
blits only the leftmost `current_width` pixels of the pre-scaled progress
surface. This is O(1) regardless of bar width and produces pixel-perfect
edges.

---

## `class MainMenu` — `game_func/main_menu.py`

### `__init__(self, data_loader, heading_font, body_font, click_sound=None)`

Reads `assets/ui/menu_config.json` to define buttons. If the file is missing,
it falls back to a hard-coded list of three buttons: **START GAME**, **Reset
Data**, **EXIT GAME**. This JSON-driven approach lets non-programmers adjust
button text, sizes, or ordering without touching Python.

Each button entry may specify an `"image"` path. If the file exists, it is
loaded as the button texture; otherwise the button falls back to a coloured
rectangle. This hybrid system supports both image-based and code-generated
buttons on a per-button basis.

### Layout strategy: bottom-left anchoring

```python
margin_x = 20
margin_bottom = 20
spacing = 6
total_height = sum(button["height"] for button in self.buttons_data) + spacing * (len(self.buttons_data) - 1)
start_y = self.VIRTUAL_H - margin_bottom - total_height
```

Buttons are stacked vertically in the bottom-left corner of the **virtual**
canvas (1366×768), not the real screen. This is why `MainMenu` is one of the
few screens that actually uses the virtual-resolution system: it calls
`data_loader.get_virtual_mouse_pos()` to translate real mouse coordinates into
virtual space before hit-testing.

### `draw(self, target_surface=None)`

Draws the background image, the title "GAKI PELZOM" with a 2-pixel drop
shadow, and then each button. Buttons support three visual states:

- **Idle:** drawn at rest position.
- **Hover:** shifted up by 1 pixel (subtle lift effect) and tinted lighter
  via `BLEND_RGB_ADD`.
- **Pressed:** shifted down-right by `(1, 2)` pixels and darkened via
  `BLEND_RGB_SUB`.

These micro-animations give the menu tactile feedback without requiring
external animation libraries.

### `handle_events(self, event)`

Only responds to `MOUSEBUTTONUP` (not `MOUSEBUTTONDOWN`). This is a deliberate
UX choice: a player who clicks down on a button, drags off, and releases
should not trigger the action. The return value is one of `"start"`,
`"reset"`, or `"quit"`, which `main.py` consumes in its state-transition
block.

---

## `class Panel` — `game_func/ui_panel.py`

The district information sidebar that appears on the right side of the map
when a district is selected.

### `__init__(self, ...)`

Loads `panel.png`, `button.png`, and `back_button.png` as textures. All three
have solid-colour fallbacks. The panel width/height are dynamic based on text
content, but capped at `max_width` / `max_height` derived from screen
resolution ratios.

### `_rebuild_panel_cache(self, district_name)`

This is the optimisation that makes the sidebar cheap to draw. Instead of
re-rendering text and re-scaling the panel image every frame, `Panel`
rebuilds its cached surfaces **only when `district_name` changes**:

1. Fetches district data via `data_loader.get_district_data()`.
2. Renders four text surfaces: name (heading), population, stats line
   (`Econ | Env | Cul | Gov`), and wrapped description.
3. Computes `panel_w` and `panel_h` from the largest line width and total
   line height, clamped to screen bounds.
4. Scales `panel.png` to those dimensions and stores the result.
5. Stores all text surfaces in `self.cached_lines`.

Because district selection changes at most a few times per minute, this
cache eliminates 99% of the text-layout work during the map loop.

### `draw_panel(self)`

Every frame:
1. Draws the back button (top-left) with alpha 180 if hovered, 255 if not.
2. If no district is selected, returns early.
3. If the cached panel exists, blits it and then blits each cached text line
   centred inside the panel.
4. Draws the BEGIN button (bottom-right) with hover alpha.

The back button and BEGIN button are hit-tested in `handle_events()`, not
inside `draw_panel()`, maintaining the project's separation of "render" and
"input".

### `handle_events(self, event)`

Returns `"back"` if the back button was clicked, `"begin"` if the BEGIN
button was clicked (and a district is selected), or `None`. `main.py` uses
this return value to decide whether to return to the menu or launch the game
scene.

---

## `class GameScene` — `game_func/game_scene.py`

The most complex renderer in the project. It handles:
- The turn-based decision screen (scenario title, description, 2–3 option
  buttons, advisor hover hints).
- The animated pillar counters (spinning numbers).
- The 2-second "ghost" feedback phase.
- The end-of-game report screen with a Matplotlib trajectory graph.

### Quadrant layout

The screen is divided into four conceptual quadrants:
- **Top-left:** the info panel showing current pillar values.
- **Top-right:** scenario title, description, and advisor quotes.
- **Bottom-left & bottom-right:** the choice option buttons (dynamically split
  into equal horizontal slices based on how many options the scenario has).

This is not enforced by Pygame containers — it is just a convention that
`draw_scenario()` and `display_info()` agree on through hard-coded rect math.

### `display_info(self, game_state_instance)` — animated counters

Each pillar (`economy`, `environment`, `culture`, `governance`) gets a
"slot-machine" counter:

- On first sight of a pillar, or when its target value changes, the counter
  enters a **spinning** state for `initial_spin_time` (3.0 s on first load,
  `update_spin_time` 1.0 s on subsequent updates).
- While spinning, the displayed text is a random 3-digit number refreshed every
  `flip_speed` (0.04 s). A click sound plays on each flip, throttled by
  `sound_rhythm` (0.05 s) so rapid flips don't stack audio.
- When the spin duration elapses, the display snaps to the true target value
  (zero-padded to 3 digits) and a deeper "lock" sound plays.
- `self.scenario_locked` remains `True` while any counter is spinning. This
  blocks `handle_choice()` from accepting clicks, preventing the player from
  making a decision before the numbers have finished their dramatic reveal.

The counters are stored in `self.counters` as a dict keyed by pillar name,
with sub-keys for target, display text, timing, and spin state. This allows
per-pillar independent animation: if economy changes but culture doesn't,
only economy spins.

### `draw_scenario(self, scenario, hover_index=None)`

Renders the decision UI. Key behaviours:

- **Option shuffling:** `options` are copied and `random.shuffle()`'d when the
  scenario ID changes. This prevents players from memorising "Option A is always
the economy boost" and gaming the system. The shuffle is cached in
`self._shuffled_options` so the order stays stable while the scenario is on
screen.

- **Dynamic button sizing:** the bottom half of the screen is divided into
`len(options)` equal vertical strips. Each strip gets a coloured rectangle
(red, blue, or green from a fixed palette) with rounded corners
(`border_radius=20`), and the option text is word-wrapped and centred inside.

- **Advisor hints:** if `hover_index` is provided, the description text is
replaced by the advisor quotes for that option. Each quote is prefixed by the
advisor's role (`"Economist: ..."`, `"Ranger: ..."`, `"Monk: ..."`). This
encourages players to hover before committing, adding a light strategic layer.

### Ghost feedback system

When the player clicks an option, `handle_choice()` returns the effect dict
to `main.py`, which immediately calls `set_ghost_feedback()` and sets
`ghost_active = True`.

`draw_scenario()` detects `ghost_active` and delegates to `_draw_ghost_state()`:

1. The selected option's box fades to white with an alpha calculated from
   elapsed time: `alpha = max(0, 255 - int((elapsed / duration) * 200))`.
2. The other options grey out to `(200, 200, 200)`.
3. The feedback text (e.g., `"Economy flourishes. Culture suffers."`) is
   rendered in green and centred in the top-right quadrant.

After `ghost_duration` (2.0 seconds), `ghost_active` becomes `False`. On the
next frame, `main.py` detects this and finally calls `game_state.apply_choice()`,
committing the numeric consequences. This creates the narrative pause that the
README describes: the player sees *what happened* before the numbers change.

### `handle_choice(self, event, mousePos)`

Returns `None` if:
- The ghost is active.
- `scenario_locked` is `True` (counters still spinning).
- A 1.0-second click cooldown has not elapsed since the last choice (prevents
double-clicks).

Otherwise, it iterates `self.choice_buttons` (populated by `draw_scenario()`)
and returns the data dict of the first button whose rect contains the mouse
position. It also triggers the ghost animation by calling
`trigger_ghost(selected_index, ...)`.

### `render_matplotlib_graph(self, history, width, height)`

Uses `matplotlib` with the `Agg` (non-interactive) backend to draw a line
graph of the 15-turn journey:

- X-axis: turns 0–15.
- Y-axis: score 0–100.
- Four dashed lines for the pillars, one solid bold line for GNH Index.
- Colours are pulled from `self.pillar_colors`.

The figure is rendered to an RGBA buffer via `FigureCanvasAgg`, then converted
to a Pygame `Surface` with `pygame.image.frombuffer()`. The figure is always
closed with `plt.close(fig)` to prevent memory leaks from accumulating
unrendered Matplotlib figures.

This method is only called from `draw_end_screen()`, so the graph is
generated once per end-screen visit, not every frame.

### `draw_end_screen(self, gameState)`

A multi-section static report:
1. Title: "5-Year Report".
2. Final GNH score in large green text.
3. Grade sentence and colour (Excellent ≥80, Good ≥60, Struggling ≥40,
   Critical <40).
4. Right-hand panel: the four final pillar values in their respective colours.
5. Left/center: the Matplotlib trajectory graph.
6. Back button (top-left) to return to the map.

A success sound plays once on entry (`end_sound_played` guard).

---

## Shared patterns across all UI classes

### Asset loading with fallbacks
Every class that loads images wraps the load in a `try/except` and constructs
a solid-colour `pygame.Surface` of the expected size if the file is missing.
This means the game is always runnable even if the `assets/` folder is stripped
down — it just looks plain.

### Colour constants
There is no central theme registry. Each module hard-codes its own colours
(e.g., `'#fff0f1'` background, `'#1B7A3F'` green text, pillar-specific RGB
tuples). For a project of this size, the duplication is acceptable; a central
`theme.py` would be the next refactor if the palette ever needs to change.

### Immediate-mode rendering
No UI class retains a "scene" or invalidates regions. Every frame, the active
screen clears and redraws everything. This is simple but means care must be
taken not to create new `Surface` objects inside hot loops (hence the caching
in `Panel._rebuild_panel_cache()` and `GameScene`'s counter dict).

### Sound generation
`GameScene.create_sound()` synthesises placeholder SFX using `numpy` sine
waves when WAV files are missing. This is a clever self-healing mechanism:
the game has audio feedback even without the `assets/sounds/` directory,
though the generated tones are primitive beeps rather than polished effects.
