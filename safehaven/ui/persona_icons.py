"""Canvas-drawn character icons and the CharacterAvatar widget.

All drawing functions take ``(canvas, cx, cy, size)`` where *cx/cy* is the
centre of the bounding circle and *size* is its diameter.  They work at any
scale from 32 px (message row avatars) to 80 px (persona selection cards).
"""

from __future__ import annotations

import math
from typing import Any, Callable

from kivy.graphics import Color, Ellipse, Line, RoundedRectangle, Triangle
from kivy.uix.widget import Widget

from safehaven.personas import PERSONAS


def _hex_to_rgba(hex_color: str) -> list[float]:
    """Convert a hex colour string to Kivy RGBA (0–1 floats)."""
    h = hex_color.lstrip("#")
    return [int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4)] + [1.0]


# ---------------------------------------------------------------------------
# Drawing functions
# ---------------------------------------------------------------------------


def draw_default_shield(canvas: Any, cx: float, cy: float, size: float) -> None:
    """SafeHaven shield — indigo dome on top, pointed base."""
    indigo = _hex_to_rgba("#5C6BC0")
    half = size * 0.30          # half-width of the shield body
    top_h = size * 0.38         # height of the domed rectangle
    tip_drop = size * 0.32      # how far the point drops below the body base

    body_x = cx - half
    body_y = cy - size * 0.08   # centre the shape on cy

    with canvas:
        Color(*indigo)
        # Domed top section — radius=[half] gives a perfect semicircle top
        RoundedRectangle(
            pos=(body_x, body_y),
            size=(half * 2, top_h),
            radius=[half, half, 0, 0],
        )
        # Pointed bottom triangle
        Triangle(
            points=[
                body_x,          body_y,           # bottom-left of body
                body_x + half * 2, body_y,          # bottom-right of body
                cx,              body_y - tip_drop,  # pointed tip
            ]
        )
        # Inner accent ring (white, 30 % opacity) for depth
        Color(1.0, 1.0, 1.0, 0.30)
        Line(
            rounded_rectangle=(
                body_x + 4, body_y + 4,
                half * 2 - 8, top_h - 8,
                half - 4,
            ),
            width=1.2,
        )


def draw_iroh_teacup(canvas: Any, cx: float, cy: float, size: float) -> None:
    """Uncle Iroh's teacup — cup body, handle arc, rim line, and steam wisps."""
    gold = _hex_to_rgba("#C8963E")
    steam = gold[:3] + [0.5]    # 50 % alpha for steam

    cup_w = size * 0.60
    cup_h = size * 0.38
    cup_x = cx - cup_w / 2
    cup_y = cy - size * 0.26    # shift cup down a bit so steam fits above
    cup_top_y = cup_y + cup_h

    with canvas:
        # Cup body
        Color(*gold)
        RoundedRectangle(
            pos=(cup_x, cup_y),
            size=(cup_w, cup_h),
            radius=[size * 0.06],
        )
        # Rim line across the top of the cup
        Line(
            points=[cup_x, cup_top_y, cup_x + cup_w, cup_top_y],
            width=1.5,
        )
        # Handle: partial ellipse arc on the right side of the cup
        handle_x = cup_x + cup_w - size * 0.01
        handle_y = cup_y + cup_h * 0.15
        handle_w = size * 0.22
        handle_h = cup_h * 0.70
        Line(
            ellipse=(handle_x, handle_y, handle_w, handle_h, -90, 90),
            width=1.5,
        )
        # Steam wisp 1 (left-of-centre)
        Color(*steam)
        sx1 = cx - size * 0.10
        Line(
            bezier=[
                sx1,              cup_top_y + size * 0.02,
                sx1 - size * 0.05, cup_top_y + size * 0.10,
                sx1 + size * 0.05, cup_top_y + size * 0.19,
                sx1,              cup_top_y + size * 0.27,
            ],
            width=1.2,
        )
        # Steam wisp 2 (right-of-centre)
        sx2 = cx + size * 0.08
        Line(
            bezier=[
                sx2,              cup_top_y + size * 0.02,
                sx2 + size * 0.05, cup_top_y + size * 0.10,
                sx2 - size * 0.05, cup_top_y + size * 0.19,
                sx2,              cup_top_y + size * 0.27,
            ],
            width=1.2,
        )


def draw_baymax_face(canvas: Any, cx: float, cy: float, size: float) -> None:
    """Baymax's iconic face — two dot eyes and one thin connecting line."""
    charcoal = _hex_to_rgba("#363641")
    er = size * 0.065           # eye radius
    eye_sep = size * 0.13       # horizontal distance from centre to each eye

    with canvas:
        Color(*charcoal)
        # Left eye
        Ellipse(
            pos=(cx - eye_sep - er, cy - er),
            size=(er * 2, er * 2),
        )
        # Right eye
        Ellipse(
            pos=(cx + eye_sep - er, cy - er),
            size=(er * 2, er * 2),
        )
        # Connecting line
        Line(
            points=[cx - eye_sep, cy, cx + eye_sep, cy],
            width=1.5,
        )


def draw_naruto_spiral(canvas: Any, cx: float, cy: float, size: float) -> None:
    """Uzumaki spiral — Archimedean spiral computed from parametric equations."""
    turns = 3
    pts_per_turn = 34           # ≈ 102 points total
    total = turns * pts_per_turn
    max_r = size * 0.44

    pts: list[float] = []
    for i in range(total):
        t = i / total
        angle = t * turns * 2.0 * math.pi
        r = t * max_r
        pts.append(cx + r * math.cos(angle))
        pts.append(cy + r * math.sin(angle))

    with canvas:
        Color(*_hex_to_rgba("#F66C2D"))
        Line(points=pts, width=2)


# ---------------------------------------------------------------------------
# Draw-function registry
# ---------------------------------------------------------------------------

_DrawFunc = Callable[[Any, float, float, float], None]

_DRAW_FUNCS: dict[str, _DrawFunc] = {
    "default": draw_default_shield,
    "iroh":    draw_iroh_teacup,
    "baymax":  draw_baymax_face,
    "naruto":  draw_naruto_spiral,
}


# ---------------------------------------------------------------------------
# CharacterAvatar widget
# ---------------------------------------------------------------------------


class CharacterAvatar(Widget):
    """Circular avatar that canvas-draws the active persona's character icon.

    Usage::

        av = CharacterAvatar(size_hint=(None, None), size=(40, 40))
        av.set_persona("iroh")

    The widget redraws itself whenever its size or position changes, so it
    works correctly at 32 px (message rows), 40 px (header), and 80 px
    (persona selection cards).
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._persona_key: str = "default"
        self.bind(size=self._redraw, pos=self._redraw)

    def set_persona(self, key: str) -> None:
        """Switch to a different persona icon and redraw immediately."""
        self._persona_key = key
        self._redraw()

    def _redraw(self, *_args: object) -> None:
        self.canvas.clear()
        if self.width < 4 or self.height < 4:
            return

        cx: float = self.center_x
        cy: float = self.center_y
        diam: float = min(self.width, self.height)
        r: float = diam / 2.0

        persona = PERSONAS.get(self._persona_key, PERSONAS["default"])
        primary_rgba = _hex_to_rgba(persona.colors["primary"])
        accent_rgba  = _hex_to_rgba(persona.colors["accent"])

        # Lighter tint of primary colour for the circle background (55 % toward white)
        bg: list[float] = [c + (1.0 - c) * 0.55 for c in primary_rgba[:3]] + [1.0]

        with self.canvas:
            # Background circle
            Color(*bg)
            Ellipse(pos=(cx - r, cy - r), size=(diam, diam))
            # Accent border ring
            Color(*accent_rgba)
            Line(circle=(cx, cy, r - 1.0), width=1.5)

        # Draw the character icon (uses 65 % of the avatar diameter)
        fn = _DRAW_FUNCS.get(self._persona_key, draw_default_shield)
        fn(self.canvas, cx, cy, diam * 0.65)
