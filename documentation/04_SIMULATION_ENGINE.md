# 4. Simulation Engine — `game_func/game_state.py`, `game_func/scenario_engine.py`, `game_func/crisis_engine.py`

## Purpose of these modules

Together, these three classes form the *rules engine* of the game — everything
that is not drawing or input. They answer three distinct questions:

1. **What is the current state of the world?** → `GameState`
2. **What policy scenario should the player face next?** → `ScenarioEngine`
3. **Has a hidden-stat threshold been breached, triggering an emergency?** → `CrisesEngine`

They are deliberately ignorant of Pygame. `GameState` stores plain Python
numbers and strings; `ScenarioEngine` and `CrisesEngine` read JSON files and
return plain dicts. This separation means the simulation could theoretically be
unit-tested (or even played as a text-only prototype) without importing
`pygame` at all.

---

## `class GameState` — `game_func/game_state.py`

### `__init__(self, data_loader_instance)` and `reset(self)`

`GameState` is instantiated once in `main.py` and reused across runs via
`reset()` rather than reconstruction. This avoids re-importing modules or
re-allocating large structures. `reset()` zeroes out:

- `turn = 0` — the game counts 0 through 14 (15 total decisions), then ends.
- `yearly_snapshots` — end-of-year deep copies for the final report.
- `history` — per-turn records used by the Matplotlib graph.
- `flags` — a `set()` of string tokens like `"fiber_optic_internet"` that
  gate future scenarios.
- `pending_effects` — currently unused in the live code, but reserved for
  a future delayed-effect scheduler.
- `played_scenarios` — a `set()` of scenario IDs already shown this run.
- `pillars` and `hidden` — empty until `receive_data()` populates them.

### `receive_data(self, district_data)`

This is the bridge between the JSON save file and the live simulation. When
the player clicks **BEGIN** on the map, `main.py` passes the selected
district's dict (from `DataLoader.get_district_data()`) into this method.

It performs **defensive normalisation** because the JSON structure has evolved
over the project:

```python
if "starting_gnh" in district_data:
    gnh_source = district_data["starting_gnh"]
elif "pillars" in district_data:
    gnh_source = district_data["pillars"]
else:
    gnh_source = district_data
```

This fallback chain means the code works whether the JSON uses the
`starting_gnh` key (the current schema), an older `pillars` key, or even a
flat district dict. The same pattern applies to `hidden_vars` / `hidden`.

Values are cast to `float` and defaulted to sensible midpoints (`50` for
pillars, `0` for most hidden stats, `50` for `public_trust`) so a malformed
or partially-edited JSON file doesn't crash the game — it just starts the
district at average values.

After loading, it immediately calls `record_snapshot()` so Turn 0 appears on
the final graph.

### `get_gnh(self)` and `get_year(self)`

- `get_gnh()` returns the arithmetic mean of the four pillars. This is the
  single score that determines victory/loss on the end screen.
- `get_year()` maps turns to in-fiction years: turns 1–3 = Year 1, 4–6 =
  Year 2, etc. It is used purely for labelling; the simulation logic itself
  operates in turns.

### `record_snapshot(self)`

Appends (or overwrites) a dict to `self.history`:

```python
{
    'turn': self.turn,
    'year': self.get_year(),
    'economy': round(..., 1),
    'environment': round(..., 1),
    'culture': round(..., 1),
    'governance': round(..., 1),
    'gnh_index': round(self.get_gnh(), 1)
}
```

If `history[-1]['turn'] == self.turn`, the last entry is replaced rather
than appended. This prevents duplicate entries when `record_snapshot()` is
called multiple times in the same turn (e.g., once after choice application
and once after passive decay).

### `apply_passive_decay(self)`

This is the "invisible hand" that punishes neglected hidden stats. It runs
automatically inside `apply_choice()` after every non-crisis decision. Each
rule checks a hidden threshold and, if exceeded, subtracts from one or more
pillars:

| Hidden stat threshold | Pillar(s) damaged | Formula |
|---|---|---|
| `corruption_index > 50` | Governance | `(index - 50) // 10` |
| `public_trust < 30` | Culture | `(30 - trust) // 5` |
| `ecological_stress > 60` | Environment | `(stress - 60) // 5` |
| `social_unrest > 60` | Governance + Economy | `(unrest - 60) // 5` each |
| `foreign_influence > 70` | Culture + Governance | `(influence - 70) // 5` each |

All results are floored with `max(0.0, ...)` so pillars never go negative.
The integer-division (`//`) means decay happens in discrete steps: e.g.,
corruption must reach 60 before governance drops by 1 point, 70 before it
drops by 2, etc. This creates a "grace region" where hidden stats can wobble
without immediate visible consequence, but once they cross into the danger
zone the damage accelerates.

### `apply_choice(self, choice_effects, is_crisis=False)`

The central state-mutation method. It receives a choice dict (from
`decisions.json` or `crises.json`) and applies its numerical consequences:

1. **Pillar adjustments:** every entry in `effects['pillars']` is added to the
corresponding pillar and clamped to `[0.0, 100.0]`.

2. **Hidden adjustments:** the same for `effects['hidden']`.

3. **Flag mutations:** `set_flags` and `remove_flags` are processed at the
   **top level of the choice dict**, not inside `effects`. This is an
   important quirk documented in the source comments: the JSON authors
   naturally put flags next to effects, but the code deliberately looks for
   them one level up so that `effects` remains a pure numeric container.

4. **Turn advancement:** if `is_crisis` is `False`, the turn counter
   increments by 1, passive decay fires, and a year-end snapshot is saved
   every third turn. If `is_crisis` is `True`, **none of these happen**.
   Crises are "free" interrupts — they don't consume your turn budget, which
   makes them feel urgent but not punishing to the 15-turn clock.

5. **Snapshot:** `record_snapshot()` is called regardless of crisis status so
   the graph always reflects the latest state.

### `save_snapshot(self)`

Deep-copies the current pillar dict and GNH into `yearly_snapshots`. This is
called at the end of every third turn (Year boundaries) and is used by the
end-screen report to show year-by-year performance.

### `update_scenario_details(self, scenario_id)`

Adds the scenario's ID string to `played_scenarios`. This set is passed back
to `ScenarioEngine.filter_deck()` to prevent duplicates within a single run.

### `get_final_state(self)`

Packages the current pillars, hidden stats, played scenarios, and flags into
a clean dict. This is what `DataLoader.save_district_data()` writes to disk
at the end of a run, so the next playthrough resumes from these exact values.

---

## `class ScenarioEngine` — `game_func/scenario_engine.py`

### `__init__(self, json_path)`

Loads `data/decisions.json` once. If the file is missing, it falls back to an
empty `{"decisions": []}` structure so the game doesn't crash — it simply
has no scenarios to show (the player would see a blank screen, but the
program stays alive).

### `filter_deck(self, current_turn, played_scenarios, flags)`

This is the scenario picker. It uses a **three-pass fallback** so that the
game never runs out of content prematurely, while still respecting author
intent when possible:

**Pass 1 — Strict match:**
- Scenario ID is not in `played_scenarios`.
- `min_turn <= current_turn <= max_turn`.
- All `required_flags` are present in the player's flag set.
- No `forbidden_flags` are present.

If any scenarios satisfy all four constraints, one is chosen uniformly at
random and returned.

**Pass 2 — Turn range only:**
- Same as Pass 1, but flag requirements are ignored.

This ensures that if the player has (or hasn't) acquired a flag that gates a
scenario, they still see *something* appropriate for their current turn range.

**Pass 3 — Global fallback:**
- Any unplayed scenario, regardless of turn or flags.

This is the safety net. Even if the JSON author mis-configured turn ranges
or the player somehow bypassed flag prerequisites, the game continues until
literally every scenario has been played.

### `_lock_and_return(self, scenario, turn)` and `clear_lock(self)`

`filter_deck()` caches its chosen scenario in `self.locked_scenario` and
`self.locked_turn`. If the method is called again on the same turn (e.g.,
because `main.py` polls it every frame), it returns the cached dict instead
of re-rolling. This prevents the scenario from changing mid-turn if the
player's flags shift (which shouldn't happen without a choice, but the guard
is cheap insurance).

`clear_lock()` is called by `main.py` immediately after a choice is applied,
freeing the engine to pick a new scenario for the next turn.

---

## `class CrisesEngine` — `game_func/crisis_engine.py`

### `__init__(self, json_path)`

Loads `data/crises.json`. Like `ScenarioEngine`, it falls back to an empty
structure on file error.

### `reset(self)`

Clears `played_crises`, `locked_crisis`, and `cooldown`. Called at the start
of every new run so crises from a previous campaign don't leak into the next.

### `check_crises(self, game_state)`

The crisis detector. It runs every time `main.py` needs a new event (both at
the start of a run and after every choice resolution). The logic is:

1. **Lock check:** if `self.locked_crisis` is not `None`, return it
   immediately. A crisis, once triggered, stays on screen until the player
   makes a choice — it cannot be skipped or replaced by a normal scenario.

2. **Cooldown check:** if `self.cooldown > 0`, decrement it and return
   `None`. This prevents back-to-back crises, giving the player at least two
   normal turns to recover between emergencies.

3. **Condition evaluation:** for every crisis in the JSON:
   - Skip if its ID is already in `played_crises` (no repeats within a run).
   - Skip if its `trigger.type` is unrecognised.
   - Build a unified `stats_source` dict from either `game_state.pillars`,
     `game_state.hidden`, or both combined, depending on `trigger.type`.
   - For every condition key (e.g., `"economy"` or `"corruption_index"`),
     check `"max"` (value must be ≤ threshold) and/or `"min"` (value must be
     ≥ threshold). All conditions must be satisfied.
   - If every condition passes, the crisis is added to `matching`.

4. **Selection:** if `matching` is non-empty, pick one at random, store it in
   `self.locked_crisis`, and return it.

The random selection means that if multiple crises qualify simultaneously
(e.g., both `economy ≤ 25` and `corruption_index ≥ 60` are true), the player
sees only one of them — whichever wins the dice roll. The others remain
unplayed and may trigger later if their conditions still hold after the
cooldown expires.

### `resolve_crisis(self, crisis_id=None)`

Called by `main.py` after the player makes a choice on a crisis screen. It:
- Adds the crisis ID to `played_crises`.
- Clears `locked_crisis` so new crises can be evaluated again.
- Sets `cooldown = 2`, meaning the next two calls to `check_crises()` will
  return `None` even if thresholds are still breached.

The cooldown is what makes crises feel like dramatic punctuation rather than
an oppressive treadmill: the player gets breathing room to fix the underlying
stats before another emergency fires.

---

## How the three classes interact in the turn loop

```text
main.py
   │
   ├─► ScenarioEngine.filter_deck(turn, played_scenarios, flags)
   │      ├─ Pass 1 (strict) → scenario dict
   │      └─ or Pass 2/3 fallback
   │
   ├─► GameScene draws scenario, player clicks option
   │
   ├─► (ghost phase: 2 seconds)
   │
   ├─► GameState.apply_choice(effects, is_crisis=False)
   │      ├─ update pillars & hidden
   │      ├─ set/remove flags
   │      ├─ apply_passive_decay()
   │      ├─ turn += 1
   │      └─ record_snapshot()
   │
   ├─► GameState.update_scenario_details(id) → played_scenarios.add(id)
   ├─► ScenarioEngine.clear_lock()
   │
   └─► CrisesEngine.check_crises(game_state)
          ├─ if match → return crisis dict (interrupt next turn)
          └─ else → None (normal scenario next turn)
```

If `CrisesEngine` returns a crisis instead of `None`, the flow is identical
except `is_crisis=True` is passed to `apply_choice()`, which skips turn
advancement and passive decay. After the choice, `CrisesEngine.resolve_crisis()`
is called instead of `ScenarioEngine.clear_lock()`.

---

## Design decisions worth noting

### Why does `GameState` own both pillars and hidden stats?

An alternative architecture would split them into two objects. Keeping them in
one place simplifies `apply_choice()` (one method updates everything) and makes
`get_final_state()` trivial. The downside is that `GameState` becomes a
"god object" for simulation data, but the project is small enough that this
is manageable.

### Why are crises checked *after* every choice rather than continuously?

Continuous checking (e.g., every frame) would be wasteful — stats only change
when a choice is applied. By checking exactly once per turn transition,
`CrisesEngine` guarantees that a crisis always appears at a natural decision
boundary, never interrupting a ghost animation or mid-render frame.

### Why does `ScenarioEngine` use a three-pass fallback instead of a single query?

The JSON content is hand-authored. Turn ranges and flag prerequisites are
design tools to create narrative pacing (early-game scenarios about
infrastructure, late-game about consequences). But if the author forgets to
cover a turn, or the player never triggers a required flag, a strict-only
engine would return `None` and stall the game. The fallback passes ensure
robustness without sacrificing authored intent when it is satisfiable.
