# Unlimited worlds

Minimal step-based grid engine core for Python.

This project aims to be a clean, extensible foundation for:
- grid-based turn-based games (roguelike-style)
- simulation sandboxes
- shared "worlds" authored by different people

The core stays **engine-only**: world state + agents + stepping.  
Rendering, networking, and ML tooling are intentionally **out of scope** and should live in separate packages.

---

## Status

**Early draft / v0.1.0**

Right now the library provides:
- `Grid` with extensible `Tile` types (`Floor`, `Wall`)
- `World` with `spawn()` and `tick()`
- `Agent` that can enqueue an `Action` via `act()`
- `Action` helpers: `move(direction)` and `wait()`
- `Event` + `WorldState` snapshot returned from `tick()`

---

## Design goals

- **Simple public API**: small surface area, easy to learn
- **Extensible by users**: custom tiles and later custom rules/systems
- **Deterministic stepping**: clear tick boundary (good for replay/testing later)
- **No "stringly-typed" commands**: actions are structured, not free-form dict protocols

---

## Install

### Development install (recommended while hacking)
From repo root:

```bash
python -m venv .venv
# Windows PowerShell:
#   .\.venv\Scripts\Activate.ps1
# macOS/Linux:
#   source .venv/bin/activate

pip install -e .
```

Editable install means you **do not reinstall** after every code change.

---

## Quick example

```python
import unlimitedworlds as uw

# 1) Build a grid
grid = uw.Grid(10, 10)
grid.set((3, 3), uw.Wall())  # non-walkable tile

# 2) Create a world
world = uw.World(grid)

# 3) Create agents independently, then spawn into the world
a1 = uw.Agent()
a2 = uw.Agent()
world.spawn(a1, at=(1, 1))
world.spawn(a2, at=(2, 1))

# 4) Queue actions for the next tick
a1.act(uw.move(uw.E))  # move east by 1 tile
a2.act(uw.wait())

# 5) Advance simulation by one tick
out = world.tick()

print("tick:", out.state.tick)
print("positions:", out.state.positions)  # {agent_uid: (x, y)}
print("events:", [(e.name, e.data) for e in out.events])
```

---

## Core concepts

### Grid / Tile
`Grid` owns the map topology and answers "can an agent occupy this tile?".

Base tiles:
- `Floor` — walkable
- `Wall` — not walkable

You can extend tile types by subclassing `Tile`.

### Agent
`Agent` is an entity that can exist independently of a world.
When spawned, it receives a `pos` in the world.

Agents do not "think" inside the engine.  
External code (player input, scripts, bots) calls `agent.act(...)`.

### Actions
An `Action` is a structured request applied by the world on the next `tick()`.

Built-ins:
- `move(Dir)` — attempt to move one tile in `Dir`
- `wait()` — do nothing

Directions:
- `Dir.N`, `Dir.E`, `Dir.S`, `Dir.W`
- shorthand aliases are also exported: `N`, `E`, `S`, `W`

### Tick
`world.tick()` advances simulation by exactly one step:
- collects queued actions from all agents
- applies them in a deterministic order (currently naive order)
- returns:
  - `WorldState` snapshot (positions + tick count)
  - list of `Event`s (useful for UI/logging/replay later)

---

## Extending the grid with custom tiles

Example: add a custom walkable tile type.

```python
import unlimitedworlds as uw

class Mud(uw.Tile):
    walkable = True
    def __init__(self, slow: int = 2) -> None:
        self.slow = slow

grid = uw.Grid(5, 5)
grid.set((2, 2), Mud(slow=3))
```

The base engine currently only uses `tile.walkable`.  
Additional effects (like slowdown) will be handled by future rule systems.

---

## Roadmap (short)

Planned next steps (in order):
1. Collision rule: two agents attempting to enter the same tile
2. World rules/systems extension point (without bloating the core)
3. Replay recording format (actions + seed + deterministic stepping)
4. Multi-world orchestration (session) built on top of the same World core
5. World generation interfaces (content -> runnable world)

---

## Contributing

This is early-stage. If you want to contribute:
- keep PRs small and focused
- prefer readable code over clever abstractions
- avoid adding external dependencies to the core package

---

## License

MIT (see `LICENSE`)
