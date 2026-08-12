# 3. Map & Geospatial — `game_func/districts_process.py` & `game_func/district_loader.py`

## Purpose of these modules

The map screen is the player's first meaningful interaction: a fullscreen
rendering of Bhutan's 20 districts as clickable polygons. Two classes split
the work:

- **`DistProc`** (`districts_process.py`) — the *geometry pipeline*. It runs
  **once** at startup, reads the raw GeoJSON file, and converts longitude/latitude
  coordinates into the game's internal 1366×768 virtual-canvas space. It also
  builds `shapely` `Polygon` / `MultiPolygon` objects that the game uses for
  precise mouse-hit detection.
- **`MapScreen`** (`district_loader.py`) — the *presentation & interaction layer*.
  It runs every frame while the player is on the map, drawing the polygons,
  highlighting hover/selection states, and resolving mouse clicks into district
  selections.

This split mirrors a classic "model vs. view" separation: `DistProc` owns all
spatial math and data structures; `MapScreen` owns all Pygame drawing and input.
Because `DistProc` is expensive (parsing JSON, projecting hundreds of
coordinates, constructing Shapely objects) but only happens once, separating it
keeps the per-frame map loop lightweight.

## Why a two-stage pipeline?

Bhutan's district boundaries are stored as GeoJSON — a geographic coordinate
system where X is longitude (roughly 88°E–92°E) and Y is latitude (roughly
27°N–28°N). These numbers are useless for Pygame directly. `DistProc` performs
a one-time **normalised affine transform**: it finds the overall bounding box
of all districts, maps that box into the virtual canvas while preserving aspect
ratio, and flips the Y-axis (geographic Y increases northward; screen Y
increases southward).

`MapScreen` never re-does this math. It simply reads the pre-computed screen
polygons from `DistProc.pygame_coords` and the pre-built Shapely collision
objects from `DistProc.districts`. This means the map is ready to draw
immediately after the loading screen finishes.

---

## `class DistProc` — `game_func/districts_process.py`

### `__init__(self, data_loader_instance, geojson_path)`

Construction runs in four phases:

1. **Canvas reference locking.** `DistProc` hard-codes itself to
   `data_loader.VIRTUAL_WIDTH` (1366) and `data_loader.VIRTUAL_HEIGHT` (768),
   not the real monitor resolution. This is deliberate: every other screen in
   the game (scenario options, sidebar panels, menu buttons) is authored
   against this virtual canvas, so the map must live in the same coordinate
   space to align correctly if virtual-resolution scaling is ever fully
   enabled (see [02_DATA_AND_PERSISTENCE.md](02_DATA_AND_PERSISTENCE.md)).

2. **GeoJSON ingestion.** Opens `data/bhutan_districts.geojson` and parses it
   with the standard `json` module. For every `Feature` with a `geometry` key,
   it calls `shapely.geometry.shape()` to turn the raw GeoJSON geometry dict
   into a Shapely `Polygon` or `MultiPolygon` object. It also extracts
   `properties.shapeName` (with a fallback chain inside `_get_district_name`)
   to label each geometry.

3. **Bounding-box & scaling math.**
   ```python
   self.overall_minx = min(b[0] for b in bounds)
   self.overall_miny = min(b[1] for b in bounds)
   self.overall_maxx = max(b[2] for b in bounds)
   self.overall_maxy = max(b[3] for b in bounds)
   ```
   These four values define the smallest axis-aligned rectangle that contains
   *all* districts. From this:
   - `raw_width` / `raw_height` = the geographic span.
   - `usable_width` = `VIRTUAL_WIDTH - padding - right_margin` (a 15% right
     margin is reserved so district names or a sidebar don't overlap the
     eastern edge).
   - `usable_height` = `VIRTUAL_HEIGHT - padding * 2`.
   - `final_scale` = `min(usable_width/raw_width, usable_height/raw_height)`.
     Using `min` preserves the geographic aspect ratio; the map is never
     stretched. If the screen is wider than 16:9, you get letterboxing; if
     narrower, pillarboxing — but because this is the *virtual* canvas, the
     actual monitor scaling happens later in `DataLoader.render_frame()`.
   - `x_offset` = left padding (small inset).
   - `y_offset` = vertical centering, divided by 1.3 rather than 2.0. This
     subtle bias pushes the map slightly *up* on the virtual canvas, leaving
     more room at the bottom for the "SELECT A DISTRICT" prompt rendered by
     `MapScreen.draw()`.

4. **Coordinate generation.** `_build_pygame_coords()` iterates every
   geometry, walks its exterior coordinate rings, and feeds each `(lon, lat)`
   pair through `conversion()` to produce a list of `(x, y)` integer tuples.
   The result is stored in `self.pygame_coords` as:
   ```python
   {'name': 'Thimphu', 'coords': [[(x1,y1), (x2,y2), ...]]}
   ```
   For `MultiPolygon` districts (a single administrative area made of several
   disjoint landmasses), every sub-polygon is preserved in the `coords` list.

   Simultaneously, `_build_polygons()` constructs Shapely `Polygon` or
   `MultiPolygon` objects from these *same* screen-space coordinates and stores
   them in `self.districts['Thimphu']`. These are the collision shapes used
   later by `MapScreen.check_hover()`.

### `conversion(self, raw_x, raw_y)`

```python
final_pygame_x = ((raw_x - self.overall_minx) * self.final_scale) + self.x_offset
final_pygame_y = (self.height - (raw_y - self.overall_miny) * self.final_scale) - self.y_offset
```

The X transform is standard normalisation: subtract the minimum, scale by the
uniform factor, then shift by the left margin.

The Y transform is more interesting. Because geographic latitude increases
northward but Pygame's Y-axis increases downward, the formula first scales
`(raw_y - miny)` exactly like X, then **subtracts it from `self.height`** to
flip the axis, and finally subtracts `y_offset` to apply the vertical bias.
The result is rounded to integers because Pygame's `draw.polygon` expects
pixel coordinates.

### `_get_district_name(self, props)`

A small defensive helper that looks for the key `shapeName` inside the
GeoJSON `properties` dict. GeoJSON sources vary wildly in their property
naming conventions; hard-coding one key with a fallback to `'Unknown'` means
if the upstream dataset ever changes its schema, the failure is visible (a
district named "Unknown" on the map) rather than a crash.

---

## `class MapScreen` — `game_func/district_loader.py`

### `__init__(self, data_loader_instance, DistProc_instance, font_manager_instance)`

Sets up rendering state:
- Stores references to `data_loader` (for `selected_district`, `hovered`, and
  the Pygame `screen` surface), `proc` (the `DistProc` instance), and `font`.
- Builds `self.district_cache`, a list of dicts that flatten everything
  `draw()` and `check_hover()` need into one structure:
  ```python
  {
      'name': name,
      'parts': parts,           # list of coordinate lists
      'polygon': polygon,       # Shapely object for hit-testing
      'bounds': bounds          # (minx, miny, maxx, maxy) tuple
  }
  ```
  Pre-extracting `bounds` here is crucial for performance — it avoids calling
  `polygon.bounds` inside the per-frame hot path.
- Renders the static footer text "----SELECT A DISTRICT----" once and stores
  its rect centered near the bottom of the screen.

### `draw(self, surface)`

Iterates `self.district_cache` and draws every district in a single pass:

1. **Border style selection:**
   - Selected district → red (`#FF0000`), width 6.
   - Hovered district → dark blue (`#151D60`), width 6.
   - Everything else → black (`#000000`), width 2.

2. **Per-part polygon drawing:** because a district may be a `MultiPolygon`,
   the inner loop iterates `parts` and calls `pygame.draw.polygon` twice:
   once with the fill color `#3C9134` (a forest green), once with the border
   color as an outline. This handles both simple and multi-part shapes safely.

3. **Footer text:** blits the pre-rendered "SELECT A DISTRICT" prompt.

The drawing order is fixed (the order districts appear in the GeoJSON), so
there is no explicit Z-sorting. Because Bhutan's districts are contiguous and
non-overlapping, this is fine — no two polygons occupy the same screen pixels.

### `check_hover(self)`

The mouse-hit routine. It uses a **two-stage filter** to avoid expensive
Shapely `contains()` calls:

1. **Bounding-box prune:** for each district, compare the mouse `(x, y)`
   against the pre-cached `(minx, miny, maxx, maxy)`. If the point is outside
   this rectangle, skip immediately. This rejects ~95% of districts in a
   single cheap integer comparison.

2. **Point-in-polygon test:** only if the mouse is inside the bounding box,
   construct a `shapely.geometry.Point(mouse_x, mouse_y)` and call
   `polygon.contains(point)`. The first match wins, and the loop breaks —
   districts don't overlap, so there is never a second match.

The result is stored in `self.dl.hovered` (a string district name, or `None`).
This is a *write-only* side effect: `MapScreen` doesn't return the hovered
name; it mutates `data_loader.hovered` so that `Panel.draw_panel()` can read
it to decide whether to show district info. This keeps the hover state in one
place (`DataLoader`) rather than duplicating it across modules.

### `check_click(self)`

Called from `main.py` when a left-click occurs on the map (and the click did
not hit the sidebar UI first). Implements **toggle selection**:

```python
if self.dl.hovered == self.dl.selected_district or self.dl.hovered is None:
    self.dl.selected_district = None
else:
    self.dl.selected_district = self.dl.hovered
```

Clicking the already-selected district deselects it. Clicking empty space
also deselects. Clicking a new district selects it. This simple rule feels
intuitive: the map is a "pick one or none" control, not a multi-select.

---

## Interaction between the two classes

| Concern | `DistProc` | `MapScreen` |
|---|---|---|
| Frequency | Once at startup | Every frame in `'Map'` state |
| Input | GeoJSON file on disk | Mouse position from Pygame |
| Output | Screen polygons + Shapely shapes | Rendered pixels + hover/selection state |
| Expensive ops | JSON parsing, coordinate projection, `Polygon` construction | `draw.polygon`, `contains()` (but only after bbox prune) |
| Why separate? | Spatial math is data-setup, not frame-loop | Drawing and input are frame-loop concerns |

`MapScreen` is constructed *after* `DistProc` in `main.py`, and receives the
same `DistProc` instance that `main.py` already built. This ordering guarantee
means `MapScreen.__init__` can safely read `proc.pygame_coords` and
`proc.districts` without worrying about `None` or partial state.

---

## Performance notes

- **No re-scaling at runtime:** `DistProc` computes everything in virtual
  canvas pixels. If the game window is resized, the virtual-to-screen scaling
  happens inside `DataLoader.render_frame()` (smooth-scale of the entire
  virtual surface), not by re-projecting every district polygon. This means
  map geometry is completely immune to window resizing — it is baked once.

- **Bounding-box cache:** without `bounds` pre-extraction, `check_hover()`
  would call `polygon.bounds` (a C-level Shapely property access, but still
  non-free) 20 times per frame. With the cache, it does 20 integer
  comparisons and only 1–2 `contains()` calls.

- **Single-pass draw:** every district is drawn with exactly two
  `pygame.draw.polygon` calls (fill + border). There is no overdraw, no
  transparency blending, and no surface creation inside the loop — all
  ingredients for a steady 60 FPS even on low-end hardware.
