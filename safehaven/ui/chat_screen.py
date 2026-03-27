"""Kivy chat screen — main conversation interface.

Replaces ``chat_window.py`` (Tkinter). Includes message list, input box,
send button, and emotion-colored message bubbles.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

from safehaven.ui.theme import (
    BACKGROUND_COLOR,
    EMOTION_COLORS,
    PRIMARY_COLOR,
    RISK_COLORS,
    SURFACE_COLOR,
    TEXT_COLOR,
    TEXT_SECONDARY,
)

if TYPE_CHECKING:
    from safehaven.controller.chat_controller import ChatController


def _hex_to_rgba(hex_color: str) -> list[float]:
    """Convert a hex color string to Kivy RGBA (0–1 floats)."""
    h = hex_color.lstrip("#")
    return [int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4)] + [1.0]


class _MessageBubble(Label):
    """A single chat message with a colored background."""

    def __init__(self, text: str, bg_color: str, **kwargs: object) -> None:
        super().__init__(
            text=text,
            markup=True,
            size_hint_y=None,
            text_size=(None, None),
            padding=(12, 8),
            color=_hex_to_rgba(TEXT_COLOR),
            font_size="14sp",
            **kwargs,
        )
        self._bg_color = _hex_to_rgba(bg_color)
        with self.canvas.before:
            Color(*self._bg_color)
            self._bg_rect = RoundedRectangle(
                size=self.size, pos=self.pos, radius=[8]
            )
        self.bind(size=self._update, pos=self._update, texture_size=self._update)

    def _update(self, *_args: object) -> None:
        if self.text_size[0] is not None:
            self.height = max(self.texture_size[1] + 20, 40)
        self._bg_rect.size = self.size
        self._bg_rect.pos = self.pos

class ChatScreen(Screen):
    """Main chat interface — message list, input box, send button."""

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._controller: ChatController | None = None

        from kivy.graphics import Color as GColor
        from kivy.graphics import Rectangle

        with self.canvas.before:
            GColor(*_hex_to_rgba(BACKGROUND_COLOR))
            self._bg_rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_bg, pos=self._update_bg)

        root = BoxLayout(orientation="vertical", padding=0, spacing=0)

        # FSM risk-level indicator bar (height=6, colored by current FSM state)
        self._state_bar = Widget(size_hint_y=None, height=6)
        self._state_bar_color: list[float] = _hex_to_rgba(RISK_COLORS["calm"])
        with self._state_bar.canvas:
            self._state_bar_color_inst = Color(*self._state_bar_color)
            self._state_bar_rect = Rectangle(
                size=self._state_bar.size, pos=self._state_bar.pos
            )
        self._state_bar.bind(
            size=self._update_state_bar, pos=self._update_state_bar
        )
        root.add_widget(self._state_bar)

        inner = BoxLayout(orientation="vertical", padding=10, spacing=8)

        # Scrollable message area
        self._scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=6,
        )
        self._message_list = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=6,
            padding=(4, 4),
        )
        self._message_list.bind(
            minimum_height=self._message_list.setter("height")
        )
        self._scroll.add_widget(self._message_list)
        inner.add_widget(self._scroll)

        # Input area
        input_row = BoxLayout(size_hint_y=None, height=44, spacing=6)

        self._text_input = TextInput(
            hint_text="Type a message…",
            multiline=False,
            font_size="14sp",
            size_hint=(1, 1),
        )
        self._text_input.bind(on_text_validate=self._on_send)
        input_row.add_widget(self._text_input)

        self._send_btn = Button(
            text="Send",
            size_hint_x=None,
            width=80,
            font_size="14sp",
            background_color=_hex_to_rgba(PRIMARY_COLOR),
            color=[1, 1, 1, 1],
        )
        self._send_btn.bind(on_release=self._on_send)
        input_row.add_widget(self._send_btn)

        inner.add_widget(input_row)
        root.add_widget(inner)
        self.add_widget(root)

        self._thinking_label: Label | None = None

        # Welcome message
        self._append_system("Welcome to SafeHaven. How are you feeling today?")

    def set_controller(self, controller: ChatController) -> None:
        """Inject the ChatController (Observer pattern)."""
        self._controller = controller

    # ── Interaction ────────────────────────────────────────────

    def _on_send(self, *_args: object) -> None:
        text = self._text_input.text.strip()
        if not text or self._controller is None:
            return

        self._text_input.text = ""
        self._append_message("You", text, SURFACE_COLOR)
        self._set_input_enabled(False)
        self._show_thinking()

        thread = threading.Thread(
            target=self._process_in_background, args=(text,), daemon=True
        )
        thread.start()

    def _process_in_background(self, text: str) -> None:
        assert self._controller is not None
        try:
            response = self._controller.handle_message(text)
        except Exception as exc:
            Clock.schedule_once(lambda _dt: self._on_error(str(exc)), 0)
            return

        if response is None:
            Clock.schedule_once(lambda _dt: self._show_crisis_screen(), 0)
        else:
            Clock.schedule_once(lambda _dt: self._on_response(response), 0)

    def _on_response(self, text: str) -> None:
        self._hide_thinking()

        # Pick bubble color from detected emotion
        bubble_color = "#E3F2FD"
        if self._controller is not None and self._controller.last_emotion is not None:
            bubble_color = EMOTION_COLORS.get(
                self._controller.last_emotion, "#E3F2FD"
            )

        self._append_message("SafeHaven", text, bubble_color)
        self._update_fsm_bar()
        self._set_input_enabled(True)
        self._text_input.focus = True

    def _on_error(self, msg: str) -> None:
        self._append_system(f"[Error: {msg}]")
        self._set_input_enabled(True)
        self._text_input.focus = True

    def _show_crisis_screen(self) -> None:
        if self.manager is not None:
            self.manager.current = "crisis"

    def on_crisis_dismissed(self) -> None:
        """Called by CrisisScreen when the user acknowledges the crisis info."""
        self._set_input_enabled(True)
        self._text_input.focus = True

    # ── Display helpers ────────────────────────────────────────

    def _append_message(self, sender: str, text: str, bg_color: str) -> None:
        bubble = _MessageBubble(
            text=f"[b]{sender}:[/b] {text}", bg_color=bg_color
        )
        # Set text_size after widget is added so it wraps properly
        bubble.bind(
            width=lambda inst, w: setattr(inst, "text_size", (w - 24, None))
        )
        self._message_list.add_widget(bubble)
        Clock.schedule_once(lambda _dt: self._scroll_to_bottom(), 0.05)

    def _append_system(self, text: str) -> None:
        lbl = Label(
            text=text,
            font_size="13sp",
            color=_hex_to_rgba(TEXT_SECONDARY),
            size_hint_y=None,
            height=30,
            halign="center",
        )
        lbl.bind(width=lambda inst, w: setattr(inst, "text_size", (w, None)))
        self._message_list.add_widget(lbl)

    def _scroll_to_bottom(self) -> None:
        self._scroll.scroll_y = 0

    def _set_input_enabled(self, enabled: bool) -> None:
        self._text_input.disabled = not enabled
        self._send_btn.disabled = not enabled

    def _update_bg(self, *_args: object) -> None:
        self._bg_rect.size = self.size
        self._bg_rect.pos = self.pos

    def _update_state_bar(self, *_args: object) -> None:
        self._state_bar_rect.size = self._state_bar.size
        self._state_bar_rect.pos = self._state_bar.pos

    def _update_fsm_bar(self) -> None:
        """Repaint the FSM state bar and pulse it to draw attention."""
        if self._controller is None:
            return
        fsm_state = self._controller.fsm_state
        color = _hex_to_rgba(RISK_COLORS.get(fsm_state, RISK_COLORS["calm"]))
        self._state_bar_color_inst.rgba = color
        self._state_bar_rect.size = self._state_bar.size
        # Brief animation pulse: shrink height then restore
        anim = Animation(height=2, duration=0.15) + Animation(height=6, duration=0.15)
        anim.start(self._state_bar)

    def _show_thinking(self) -> None:
        lbl = Label(
            text="SafeHaven is thinking…",
            font_size="13sp",
            color=_hex_to_rgba(TEXT_SECONDARY),
            size_hint_y=None,
            height=30,
            halign="center",
        )
        lbl.bind(width=lambda inst, w: setattr(inst, "text_size", (w, None)))
        self._thinking_label = lbl
        self._message_list.add_widget(lbl)
        Clock.schedule_once(lambda _dt: self._scroll_to_bottom(), 0.05)

    def _hide_thinking(self) -> None:
        if self._thinking_label is not None:
            self._message_list.remove_widget(self._thinking_label)
            self._thinking_label = None