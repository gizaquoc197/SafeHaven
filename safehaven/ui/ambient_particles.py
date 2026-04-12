"""AmbientParticleWidget — per-persona background particle effects.

Draws ambient particles on the chat screen canvas, behind all message
content.  Three particle types are supported (STEAM, SCAN, LEAVES); the
default persona uses NONE and never instantiates this widget.

Performance contract
--------------------
* Maximum 40 active particles at any time (3 for SCAN rings).
* Canvas instructions are pre-allocated in a pool during ``__init__``
  and reused every frame — no Kivy graphics objects are created or
  destroyed while the clock is running.
* Clock runs at 30 FPS (``1/30`` s interval).
* ``stop()`` cancels the clock and sets all canvas opacities to 0.
"""

from __future__ import annotations

import math
import random
from typing import Any

from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line
from kivy.uix.widget import Widget

from safehaven.personas.config import ParticleType

# ── Constants ──────────────────────────────────────────────────────────────

_MAX_PARTICLES = 40
_MAX_SCAN_RINGS = 3

_SPAWN_INTERVAL: dict[ParticleType, float] = {
    ParticleType.STEAM: 0.2,
    ParticleType.SCAN: 3.0,
    ParticleType.LEAVES: 0.5,
    ParticleType.NONE: 0.0,
}

# Pre-parsed leaf colours (RGBA 0–1 floats): #4CAF50, #FF9800
_LEAF_COLORS: list[list[float]] = [
    [0.298, 0.686, 0.314, 1.0],
    [1.0, 0.596, 0.0, 1.0],
]

# SCAN ring colour: #85A2B6
_SCAN_RGB: list[float] = [0.522, 0.635, 0.714]


# ── Widget ─────────────────────────────────────────────────────────────────

class AmbientParticleWidget(Widget):
    """Ambient background particle effect tied to a specific ``ParticleType``.

    Add this widget to a parent *before* adding content widgets so that it
    is drawn behind everything (Kivy renders children[-1] first).

    Usage::

        particle_widget = AmbientParticleWidget(particle_type=ParticleType.STEAM,
                                                size_hint=(1, 1))
        screen.add_widget(particle_widget, index=len(screen.children))
        particle_widget.start()
        # … later …
        particle_widget.stop()
    """

    def __init__(self, particle_type: ParticleType, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._particle_type: ParticleType = particle_type
        self._active: list[dict[str, Any]] = []
        self._spawn_timer: float = 0.0
        self._clock_event: object = None

        # Pre-allocate the canvas instruction pool once.
        self._pool: list[tuple[Color, Any]] = []
        self._init_pool()

    # ── Public API ─────────────────────────────────────────────────────────

    @property
    def particle_type(self) -> ParticleType:
        """The ``ParticleType`` this widget was constructed with."""
        return self._particle_type

    def start(self) -> None:
        """Begin the 30-FPS clock tick.  Idempotent."""
        if self._clock_event is None:
            self._clock_event = Clock.schedule_interval(self._tick, 1.0 / 30.0)

    def stop(self) -> None:
        """Cancel the clock and hide all particles.

        All canvas instructions remain in the pool (invisible) so the
        widget can be restarted cheaply by calling ``start()`` again.
        """
        if self._clock_event is not None:
            self._clock_event.cancel()  # type: ignore[attr-defined]
            self._clock_event = None
        for color, _ in self._pool:
            color.a = 0.0
        self._active.clear()
        self._spawn_timer = 0.0

    # ── Pool initialisation ────────────────────────────────────────────────

    def _init_pool(self) -> None:
        """Pre-allocate canvas instructions based on particle type."""
        if self._particle_type == ParticleType.SCAN:
            n = _MAX_SCAN_RINGS
            with self.canvas:
                for _ in range(n):
                    color = Color(*_SCAN_RGB, 0.0)
                    line = Line(circle=(0.0, 0.0, 1.0), width=1.5)
                    self._pool.append((color, line))
        else:
            n = _MAX_PARTICLES
            with self.canvas:
                for _ in range(n):
                    color = Color(1.0, 1.0, 1.0, 0.0)
                    ellipse = Ellipse(pos=(0.0, 0.0), size=(0.0, 0.0))
                    self._pool.append((color, ellipse))

    # ── Frame tick ────────────────────────────────────────────────────────

    def _tick(self, dt: float) -> None:
        """Called every ~1/30 s.  Update particles and spawn new ones."""
        dead: list[dict[str, Any]] = []

        for p in self._active:
            self._update_particle(p, dt)
            if p["age"] >= p["max_age"]:
                dead.append(p)

        for p in dead:
            color, _ = self._pool[p["pool_idx"]]
            color.a = 0.0
            self._active.remove(p)

        interval = _SPAWN_INTERVAL[self._particle_type]
        self._spawn_timer += dt
        while self._spawn_timer >= interval:
            self._spawn_timer -= interval
            self._try_spawn()

    # ── Pool helpers ──────────────────────────────────────────────────────

    def _get_free_pool_idx(self) -> int | None:
        """Return the first pool index not currently used by an active particle."""
        max_n = _MAX_SCAN_RINGS if self._particle_type == ParticleType.SCAN else _MAX_PARTICLES
        used = {p["pool_idx"] for p in self._active}
        for i in range(max_n):
            if i not in used:
                return i
        return None  # pool full

    # ── Spawn ─────────────────────────────────────────────────────────────

    def _try_spawn(self) -> None:
        idx = self._get_free_pool_idx()
        if idx is None:
            return  # pool exhausted — skip this spawn tick
        if self._particle_type == ParticleType.STEAM:
            self._spawn_steam(idx)
        elif self._particle_type == ParticleType.SCAN:
            self._spawn_scan(idx)
        elif self._particle_type == ParticleType.LEAVES:
            self._spawn_leaf(idx)

    def _spawn_steam(self, idx: int) -> None:
        # Spread across full width, rise from bottom 15% of screen
        x = self.x + random.uniform(0.05 * self.width, 0.95 * self.width)
        y = self.y + random.uniform(0.0, 0.15 * self.height)
        self._active.append(
            {
                "pool_idx": idx,
                "x": x,
                "y": y,
                "base_x": x,
                "age": 0.0,
                "max_age": random.uniform(3.0, 5.0),
                "size": random.uniform(8.0, 16.0),
                "vy": random.uniform(20.0, 35.0),
                "wobble_amp": random.uniform(8.0, 15.0),
                "wobble_freq": random.uniform(2.5, 4.2),
                "max_opacity": random.uniform(0.45, 0.65),
            }
        )

    def _spawn_scan(self, idx: int) -> None:
        max_radius = max(self.width, self.height) * 0.8
        self._active.append(
            {
                "pool_idx": idx,
                "cx": self.center_x,
                "cy": self.center_y,
                "age": 0.0,
                "max_age": 4.0,
                "max_radius": max(max_radius, 10.0),
            }
        )

    def _spawn_leaf(self, idx: int) -> None:
        x = self.x + random.uniform(0.0, max(self.width, 1.0))
        y = self.y + self.height
        leaf_color = random.choice(_LEAF_COLORS)
        self._active.append(
            {
                "pool_idx": idx,
                "x": x,
                "y": y,
                "base_x": x,
                "age": 0.0,
                "max_age": random.uniform(5.0, 8.0),
                "size": random.uniform(6.0, 10.0),
                "vy": random.uniform(30.0, 60.0),
                "wobble_amp": random.uniform(30.0, 50.0),
                "wobble_freq": random.uniform(2.09, 3.14),
                "color": leaf_color,
            }
        )

    # ── Per-particle update ───────────────────────────────────────────────

    def _update_particle(self, p: dict[str, Any], dt: float) -> None:
        p["age"] = float(p["age"]) + dt
        if self._particle_type == ParticleType.STEAM:
            self._update_steam(p, dt)
        elif self._particle_type == ParticleType.SCAN:
            self._update_scan(p)
        elif self._particle_type == ParticleType.LEAVES:
            self._update_leaf(p, dt)

    def _update_steam(self, p: dict[str, Any], dt: float) -> None:
        age: float = p["age"]
        max_age: float = p["max_age"]
        p["y"] = float(p["y"]) + float(p["vy"]) * dt
        p["x"] = float(p["base_x"]) + float(p["wobble_amp"]) * math.sin(
            age * float(p["wobble_freq"])
        )
        frac = age / max_age
        max_op: float = p["max_opacity"]
        if frac <= 0.8:
            opacity = max_op
        else:
            opacity = max_op * (1.0 - (frac - 0.8) / 0.2)
        size = float(p["size"]) * (1.0 - frac * 0.7)
        size = max(size, 0.5)
        color, ellipse = self._pool[p["pool_idx"]]
        color.rgba = [0.72, 0.52, 0.22, max(opacity, 0.0)]
        ellipse.pos = (float(p["x"]) - size / 2.0, float(p["y"]) - size / 2.0)
        ellipse.size = (size, size)

    def _update_scan(self, p: dict[str, Any]) -> None:
        age: float = p["age"]
        max_age: float = p["max_age"]
        frac = age / max_age
        radius = max(1.0, float(p["max_radius"]) * frac)
        if frac < 0.3:
            opacity = (frac / 0.3) * 0.08
        else:
            opacity = 0.08 * (1.0 - (frac - 0.3) / 0.7)
        color, line = self._pool[p["pool_idx"]]
        color.rgba = [*_SCAN_RGB, max(opacity, 0.0)]
        line.circle = (float(p["cx"]), float(p["cy"]), radius)

    def _update_leaf(self, p: dict[str, Any], dt: float) -> None:
        age: float = p["age"]
        max_age: float = p["max_age"]
        p["y"] = float(p["y"]) - float(p["vy"]) * dt
        p["x"] = float(p["base_x"]) + float(p["wobble_amp"]) * math.sin(
            age * float(p["wobble_freq"])
        )
        frac = age / max_age
        opacity = 1.0 if frac <= 0.85 else (1.0 - (frac - 0.85) / 0.15)
        size: float = p["size"]
        leaf_color: list[float] = p["color"]
        color, ellipse = self._pool[p["pool_idx"]]
        color.rgba = [leaf_color[0], leaf_color[1], leaf_color[2], max(opacity, 0.0)]
        ellipse.pos = (float(p["x"]) - size / 2.0, float(p["y"]) - size / 2.0)
        ellipse.size = (size, size)
