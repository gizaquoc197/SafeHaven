"""Insights dashboard screen — displays emotional trends over time.

Placeholder screen with navigation. Matplotlib integration deferred.
"""

from __future__ import annotations

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen

from safehaven.ui.theme import BACKGROUND_COLOR, PRIMARY_COLOR, TEXT_COLOR, TEXT_SECONDARY


def _hex_to_rgba(hex_color: str) -> list[float]:
    """Convert a hex color string to Kivy RGBA (0–1 floats)."""
    h = hex_color.lstrip("#")
    return [int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4)] + [1.0]


class InsightsScreen(Screen):
    """Placeholder insights screen with a 'Back to Chat' button."""

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)

        from kivy.graphics import Color, Rectangle

        with self.canvas.before:
            Color(*_hex_to_rgba(BACKGROUND_COLOR))
            self._bg_rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_bg, pos=self._update_bg)

        layout = BoxLayout(orientation="vertical", padding=40, spacing=20)

        layout.add_widget(Label(size_hint_y=1))

        layout.add_widget(
            Label(
                text="Emotional Insights",
                font_size="24sp",
                bold=True,
                color=_hex_to_rgba(PRIMARY_COLOR),
                size_hint_y=None,
                height=40,
            )
        )

        layout.add_widget(
            Label(
                text="Coming soon — emotional trends and session history.",
                font_size="14sp",
                color=_hex_to_rgba(TEXT_SECONDARY),
                size_hint_y=None,
                height=30,
            )
        )

        back_btn = Button(
            text="Back to Chat",
            font_size="15sp",
            size_hint=(0.4, None),
            height=44,
            pos_hint={"center_x": 0.5},
            background_color=_hex_to_rgba(PRIMARY_COLOR),
            color=[1, 1, 1, 1],
        )
        back_btn.bind(on_release=self._go_back)
        layout.add_widget(back_btn)

        layout.add_widget(Label(size_hint_y=1))

        self.add_widget(layout)

    def _go_back(self, *_args: object) -> None:
        if self.manager is not None:
            self.manager.current = "chat"

    def _update_bg(self, *_args: object) -> None:
        self._bg_rect.size = self.size
        self._bg_rect.pos = self.pos
