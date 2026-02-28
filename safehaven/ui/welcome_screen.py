"""Welcome/splash screen — first screen shown on app launch.

Displays SafeHaven branding, a brief description, and a start button.
"""

from __future__ import annotations

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen

from safehaven.ui.theme import (
    BACKGROUND_COLOR,
    PRIMARY_COLOR,
    TEXT_COLOR,
    TEXT_SECONDARY,
)


def _hex_to_rgba(hex_color: str) -> list[float]:
    """Convert a hex color string to Kivy RGBA (0–1 floats)."""
    h = hex_color.lstrip("#")
    return [int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4)] + [1.0]


class WelcomeScreen(Screen):
    """Splash screen with branding and a 'Start Chatting' button."""

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        from kivy.graphics import Color, Rectangle

        with self.canvas.before:
            Color(*_hex_to_rgba(BACKGROUND_COLOR))
            self._bg_rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_bg, pos=self._update_bg)

        layout = BoxLayout(orientation="vertical", padding=40, spacing=20)

        # Spacer top
        layout.add_widget(Label(size_hint_y=1))

        # Title
        layout.add_widget(
            Label(
                text="SafeHaven",
                font_size="32sp",
                bold=True,
                color=_hex_to_rgba(PRIMARY_COLOR),
                size_hint_y=None,
                height=50,
            )
        )

        # Subtitle
        layout.add_widget(
            Label(
                text="A safety-aware mental health chatbot",
                font_size="16sp",
                color=_hex_to_rgba(TEXT_COLOR),
                size_hint_y=None,
                height=30,
            )
        )

        # Disclaimer
        layout.add_widget(
            Label(
                text=(
                    "Disclaimer: This is a course project — not for\n"
                    "production or clinical use."
                ),
                font_size="12sp",
                color=_hex_to_rgba(TEXT_SECONDARY),
                size_hint_y=None,
                height=40,
                halign="center",
            )
        )

        # Start button
        start_btn = Button(
            text="Start Chatting",
            font_size="18sp",
            size_hint=(0.5, None),
            height=50,
            pos_hint={"center_x": 0.5},
            background_color=_hex_to_rgba(PRIMARY_COLOR),
            color=[1, 1, 1, 1],
        )
        start_btn.bind(on_release=self._go_to_chat)
        layout.add_widget(start_btn)

        # Spacer bottom
        layout.add_widget(Label(size_hint_y=1))

        self.add_widget(layout)

    def _update_bg(self, *_args: object) -> None:
        self._bg_rect.size = self.size
        self._bg_rect.pos = self.pos

    def _go_to_chat(self, *_args: object) -> None:
        if self.manager is not None:
            self.manager.current = "chat"
