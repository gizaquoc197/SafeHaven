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
from kivy.uix.widget import Widget

from safehaven.personas import PERSONAS
from safehaven.ui.persona_icons import CharacterAvatar

if TYPE_CHECKING:
    from safehaven.controller.chat_controller import ChatController


def _hex_to_rgba(hex_color: str) -> list[float]:
    """Convert a hex color string to Kivy RGBA (0–1 floats)."""
    h = hex_color.lstrip("#")
    return [int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4)] + [1.0]


class _PersonaCard(BoxLayout):
    """Single tappable persona card showing emoji, name, and description."""

    def __init__(self, key: str, on_select: object, **kwargs: object) -> None:
        super().__init__(orientation="vertical", padding=(12, 20), spacing=6, **kwargs)
        self._key = key
        self._on_select = on_select
        persona = PERSONAS[key]
        primary = persona.colors["primary"]

        # Canvas: white background, top colour strip, coloured border
        with self.canvas.before:
            Color(*_hex_to_rgba("#FFFFFF"))
            self._bg = Rectangle(size=self.size, pos=self.pos)
            Color(*_hex_to_rgba(primary))
            self._top_strip = Rectangle(
                pos=(self.x, self.top - 8), size=(self.width, 8)
            )
            Color(*_hex_to_rgba(primary))
            self._border = Line(
                rectangle=(self.x, self.y, self.width, self.height), width=2
            )
        self.bind(size=self._update_canvas, pos=self._update_canvas)

        # 80 px canvas-drawn avatar, horizontally centred
        avatar_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=88,
        )
        avatar = CharacterAvatar(size_hint=(None, None), size=(80, 80))
        avatar.set_persona(key)
        avatar_row.add_widget(Widget())
        avatar_row.add_widget(avatar)
        avatar_row.add_widget(Widget())
        self.add_widget(avatar_row)

        # Character name — bold, 18sp, persona primary colour
        self.add_widget(Label(
            text=persona.name,
            font_size="18sp",
            bold=True,
            color=_hex_to_rgba(persona.colors["primary"]),
            size_hint_y=None,
            height=26,
            halign="center",
        ))

        # Catchphrase — italic, 13sp, gray, wraps inside the card
        catch_label = Label(
            text=f"[i]{persona.catchphrase}[/i]",
            markup=True,
            font_size="13sp",
            color=_hex_to_rgba("#757575"),
            halign="center",
            valign="top",
            size_hint_y=1,
        )
        catch_label.bind(
            width=lambda inst, w: setattr(inst, "text_size", (w - 24, None))
        )
        self.add_widget(catch_label)

        # Select button
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
        self._top_strip.pos  = (self.x, self.top - 8)
        self._top_strip.size = (self.width, 8)
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

        # Top elastic spacer — balances the bottom spacer to vertically centre the cards
        root.add_widget(Widget(size_hint_y=1))

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
        grid = GridLayout(cols=len(PERSONAS), spacing=12, size_hint_y=None, height=280)
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
        """Reset session, set active persona, and navigate to chat."""
        if self._controller is not None:
            self._controller.clear()
            self._controller.active_persona = PERSONAS[key]
        if self.manager is not None:
            self.manager.current = "chat"
