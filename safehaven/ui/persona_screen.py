"""Persona selection screen — shown between WelcomeScreen and ChatScreen.

Displays one card per registered persona. Selecting a card sets the active
persona on the ChatController and navigates to the chat screen.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from kivy.graphics import Color, Line, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen

from safehaven.personas import PERSONAS

if TYPE_CHECKING:
    from safehaven.controller.chat_controller import ChatController


def _hex_to_rgba(hex_color: str) -> list[float]:
    """Convert a hex color string to Kivy RGBA (0–1 floats)."""
    h = hex_color.lstrip("#")
    return [int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4)] + [1.0]


class _PersonaCard(BoxLayout):
    """Single tappable persona card showing emoji, name, and description."""

    def __init__(self, key: str, on_select: object, **kwargs: object) -> None:
        super().__init__(orientation="vertical", padding=12, spacing=6, **kwargs)
        self._key = key
        self._on_select = on_select
        persona = PERSONAS[key]
        primary = persona.colors["primary"]

        # Colored border via canvas
        with self.canvas.before:
            Color(*_hex_to_rgba("#FFFFFF"))
            self._bg = Rectangle(size=self.size, pos=self.pos)
            Color(*_hex_to_rgba(primary))
            self._border = Line(rectangle=(self.x, self.y, self.width, self.height), width=2)
        self.bind(size=self._update_canvas, pos=self._update_canvas)

        # Emoji avatar
        self.add_widget(Label(
            text=persona.icon_emoji,
            font_size="36sp",
            size_hint_y=None,
            height=52,
            halign="center",
        ))

        # Name
        self.add_widget(Label(
            text=persona.name,
            font_size="14sp",
            bold=True,
            color=_hex_to_rgba(persona.colors["text"]),
            size_hint_y=None,
            height=22,
            halign="center",
        ))

        # Description — wraps inside the card
        desc_label = Label(
            text=persona.description,
            font_size="11sp",
            color=_hex_to_rgba(persona.colors["text"]),
            halign="center",
            valign="top",
            text_size=(self.width - 24, None),
        )
        self.bind(width=lambda _, w: setattr(desc_label, "text_size", (w - 24, None)))
        self.add_widget(desc_label)

        # Invisible tap button overlaid via a transparent Button at the bottom
        tap_btn = Button(
            text="Select",
            font_size="12sp",
            size_hint_y=None,
            height=32,
            background_color=_hex_to_rgba(primary),
            color=[1, 1, 1, 1],
        )
        tap_btn.bind(on_release=self._select)
        self.add_widget(tap_btn)

    def _update_canvas(self, *_args: object) -> None:
        self._bg.size = self.size
        self._bg.pos = self.pos
        self._border.rectangle = (self.x, self.y, self.width, self.height)

    def _select(self, *_args: object) -> None:
        if callable(self._on_select):
            self._on_select(self._key)


class PersonaScreen(Screen):
    """Grid of persona cards; navigates to chat after selection."""

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._controller: ChatController | None = None

        with self.canvas.before:
            Color(*_hex_to_rgba("#FAFAFA"))
            self._bg_rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_bg, pos=self._update_bg)

        root = BoxLayout(orientation="vertical", padding=24, spacing=16)

        # Title
        root.add_widget(Label(
            text="Choose Your Companion",
            font_size="24sp",
            bold=True,
            color=_hex_to_rgba("#212121"),
            size_hint_y=None,
            height=48,
            halign="center",
        ))

        # Subtitle
        root.add_widget(Label(
            text="Each companion brings a different therapeutic voice.\nYou can change this at any time.",
            font_size="13sp",
            color=_hex_to_rgba("#757575"),
            size_hint_y=None,
            height=36,
            halign="center",
        ))

        # Card grid — one card per persona
        grid = GridLayout(cols=len(PERSONAS), spacing=12, size_hint_y=None, height=220)
        for key in ("default", "iroh", "baymax", "naruto"):
            if key in PERSONAS:
                grid.add_widget(_PersonaCard(key=key, on_select=self._on_persona_selected))
        root.add_widget(grid)

        # Spacer
        root.add_widget(Label(size_hint_y=1))

        self.add_widget(root)

    def set_controller(self, controller: ChatController) -> None:
        """Inject the ChatController."""
        self._controller = controller

    def _update_bg(self, *_args: object) -> None:
        self._bg_rect.size = self.size
        self._bg_rect.pos = self.pos

    def _on_persona_selected(self, key: str) -> None:
        """Set active persona on the controller and navigate to chat."""
        if self._controller is not None:
            self._controller.active_persona = PERSONAS[key]
        if self.manager is not None:
            self.manager.current = "chat"
