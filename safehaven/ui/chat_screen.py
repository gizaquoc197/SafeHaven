"""Kivy chat screen — main conversation interface.

Replaces ``chat_window.py`` (Tkinter). Includes message list, input box,
send button, and emotion-colored message bubbles with left/right alignment.
"""

from __future__ import annotations

import re
import threading
from datetime import datetime
from typing import TYPE_CHECKING

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.properties import ColorProperty
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
    TEXT_COLOR,
    TEXT_SECONDARY,
)

if TYPE_CHECKING:
    from safehaven.controller.chat_controller import ChatController

_USER_BUBBLE_COLOR = "#E8EAF6"  # Material indigo-50


def _hex_to_rgba(hex_color: str) -> list[float]:
    """Convert a hex color string to Kivy RGBA (0–1 floats)."""
    h = hex_color.lstrip("#")
    return [int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4)] + [1.0]


def _lighten(hex_color: str, amount: float = 0.82) -> list[float]:
    """Blend hex_color toward white. amount=1.0 = pure white."""
    rgba = _hex_to_rgba(hex_color)
    return [c + (1.0 - c) * amount for c in rgba[:3]] + [1.0]


def _escape_kivy(text: str) -> str:
    """Escape square brackets so Kivy's markup parser treats them as literals."""
    return text.replace("[", r"\[").replace("]", r"\]")


def _md_to_kivy(text: str) -> str:
    """Convert a subset of Markdown to Kivy markup tags."""
    text = _escape_kivy(text)
    # **bold**
    text = re.sub(r"\*\*(.+?)\*\*", r"[b]\1[/b]", text, flags=re.DOTALL)
    # *italic* (negative lookaround avoids matching on **)
    text = re.sub(
        r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"[i]\1[/i]", text, flags=re.DOTALL
    )
    # ### Header lines → bold
    text = re.sub(r"^#{1,6}\s+(.+)$", r"[b]\1[/b]", text, flags=re.MULTILINE)
    return text


class _TypingDots(BoxLayout):
    """Three animated dots shown while the LLM is generating a response."""

    def __init__(self, **kwargs: object) -> None:
        super().__init__(
            orientation="horizontal",
            size_hint=(None, None),
            width=56,
            height=30,
            spacing=6,
            **kwargs,
        )
        self._running = True
        dim = _hex_to_rgba(TEXT_SECONDARY)
        self._dots: list[Label] = []
        for _ in range(3):
            dot = Label(text="●", font_size="14sp", color=list(dim))
            self.add_widget(dot)
            self._dots.append(dot)
        Clock.schedule_once(lambda _dt: self._pulse(0), 0.1)

    def _pulse(self, idx: int) -> None:
        if not self._running:
            return
        dot = self._dots[idx]
        bright: list[float] = [1.0, 1.0, 1.0, 1.0]
        dim = list(_hex_to_rgba(TEXT_SECONDARY))
        anim = Animation(color=bright, duration=0.25) + Animation(
            color=dim, duration=0.25
        )
        anim.bind(on_complete=lambda *_: self._pulse((idx + 1) % 3))
        anim.start(dot)

    def stop_animation(self) -> None:
        self._running = False
        Animation.cancel_all(self)


class _MessageBubble(Label):
    """A single chat message with a colored background."""

    def __init__(self, text: str, bg_color: str, **kwargs: object) -> None:
        super().__init__(
            text=text,
            markup=True,
            size_hint=(1, None),
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
        if self.width > 24:
            self.text_size = (self.width - 24, None)
        if self.text_size[0] is not None:
            self.height = max(self.texture_size[1] + 20, 40)
        self._bg_rect.size = self.size
        self._bg_rect.pos = self.pos


class ChatScreen(Screen):
    """Main chat interface — message list, input box, send button."""

    _bg_color_prop = ColorProperty([0.98, 0.98, 0.98, 1.0])

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._controller: ChatController | None = None
        self._thinking_widget: BoxLayout | None = None

        with self.canvas.before:
            self._bg_color_inst = Color(0.98, 0.98, 0.98, 1.0)
            self._bg_rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(
            size=self._update_bg,
            pos=self._update_bg,
            _bg_color_prop=self._apply_bg_color,
        )

        root = BoxLayout(orientation="vertical", padding=0, spacing=0)

        # FSM risk-level indicator bar (height=6, colored by current FSM state)
        self._state_bar = Widget(size_hint_y=None, height=6)
        with self._state_bar.canvas:
            self._state_bar_color_inst = Color(*_hex_to_rgba(RISK_COLORS["calm"]))
            self._state_bar_rect = Rectangle(
                size=self._state_bar.size, pos=self._state_bar.pos
            )
        self._state_bar.bind(
            size=self._update_state_bar, pos=self._update_state_bar
        )
        root.add_widget(self._state_bar)

        # Header bar: title + New Chat button
        header = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=40,
            padding=(10, 4),
            spacing=8,
        )
        with header.canvas.before:
            Color(*_hex_to_rgba("#FFFFFF"))
            self._header_rect = Rectangle(size=header.size, pos=header.pos)
        header.bind(
            size=lambda inst, v: setattr(self._header_rect, "size", v),
            pos=lambda inst, v: setattr(self._header_rect, "pos", v),
        )
        header.add_widget(Label(
            text="SafeHaven",
            font_size="16sp",
            bold=True,
            color=_hex_to_rgba(PRIMARY_COLOR),
            halign="left",
            size_hint_x=1,
        ))
        new_chat_btn = Button(
            text="New Chat",
            size_hint=(None, None),
            size=(80, 28),
            font_size="12sp",
            background_color=_hex_to_rgba("#FFFFFF"),
            color=_hex_to_rgba(PRIMARY_COLOR),
            border=(1, 1, 1, 1),
        )
        new_chat_btn.bind(on_release=self._on_new_chat)
        header.add_widget(new_chat_btn)
        root.add_widget(header)

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

        insights_btn = Button(
            text="Insights",
            size_hint_x=None,
            width=80,
            font_size="13sp",
            background_color=_hex_to_rgba("#7E57C2"),
            color=[1, 1, 1, 1],
        )
        insights_btn.bind(on_release=self._go_to_insights)
        input_row.add_widget(insights_btn)

        inner.add_widget(input_row)
        root.add_widget(inner)
        self.add_widget(root)

        # Welcome message
        self._append_system("Welcome to SafeHaven. How are you feeling today?")

    def set_controller(self, controller: ChatController) -> None:
        """Inject the ChatController (Observer pattern)."""
        self._controller = controller

    def _on_new_chat(self, *_args: object) -> None:
        """Clear conversation history and reset FSM to CALM."""
        if self._controller is not None:
            self._controller.clear()
        self._message_list.clear_widgets()
        # Reset mood background
        Animation.cancel_all(self)
        self._bg_color_prop = [0.98, 0.98, 0.98, 1.0]
        self._append_system("Welcome to SafeHaven. How are you feeling today?")

    # ── Interaction ────────────────────────────────────────────

    def _on_send(self, *_args: object) -> None:
        text = self._text_input.text.strip()
        if not text or self._controller is None:
            return

        self._text_input.text = ""
        self._append_message("You", text, _USER_BUBBLE_COLOR, is_user=True)
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

        bubble_color = "#E3F2FD"
        if self._controller is not None and self._controller.last_emotion is not None:
            bubble_color = EMOTION_COLORS.get(
                self._controller.last_emotion, "#E3F2FD"
            )

        self._append_message("SafeHaven", text, bubble_color, is_user=False)
        self._update_fsm_bar()
        self._update_mood_background()
        self._set_input_enabled(True)
        self._text_input.focus = True

    def _on_error(self, msg: str) -> None:
        self._hide_thinking()
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

    def _append_message(
        self, sender: str, text: str, bg_color: str, *, is_user: bool = False
    ) -> None:
        ts = datetime.now().strftime("%H:%M")
        display = _escape_kivy(text) if is_user else _md_to_kivy(text)
        bubble = _MessageBubble(
            text=f"[b]{sender}[/b]  [size=11][color=888888]{ts}[/color][/size]\n{display}",
            bg_color=bg_color,
            size_hint_x=0.85,
        )

        row = BoxLayout(size_hint_y=None, height=40, orientation="horizontal")
        bubble.bind(height=row.setter("height"))
        if is_user:
            row.add_widget(Widget(size_hint_x=0.15))
            row.add_widget(bubble)
        else:
            row.add_widget(bubble)
            row.add_widget(Widget(size_hint_x=0.15))

        self._message_list.add_widget(row)
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

    def _show_thinking(self) -> None:
        dots = _TypingDots()
        row = BoxLayout(size_hint_y=None, height=30, orientation="horizontal")
        row.add_widget(dots)
        row.add_widget(Widget())
        row._dots_ref = dots  # type: ignore[attr-defined]
        self._thinking_widget = row
        self._message_list.add_widget(row)
        Clock.schedule_once(lambda _dt: self._scroll_to_bottom(), 0.05)

    def _hide_thinking(self) -> None:
        if self._thinking_widget is not None:
            dots_ref = getattr(self._thinking_widget, "_dots_ref", None)
            if dots_ref is not None:
                dots_ref.stop_animation()
            self._message_list.remove_widget(self._thinking_widget)
            self._thinking_widget = None

    def _scroll_to_bottom(self) -> None:
        self._scroll.scroll_y = 0

    def _set_input_enabled(self, enabled: bool) -> None:
        self._text_input.disabled = not enabled
        self._send_btn.disabled = not enabled

    # ── Background ─────────────────────────────────────────────

    def _update_bg(self, *_args: object) -> None:
        self._bg_rect.size = self.size
        self._bg_rect.pos = self.pos

    def _apply_bg_color(self, _inst: object, value: list[float]) -> None:
        self._bg_color_inst.rgba = value

    def _update_mood_background(self) -> None:
        """Animate the background toward a lightened tint of the detected emotion."""
        if self._controller is None or self._controller.last_emotion is None:
            return
        target_hex = EMOTION_COLORS.get(self._controller.last_emotion, BACKGROUND_COLOR)
        Animation(
            _bg_color_prop=_lighten(target_hex), duration=2.5, t="in_out_sine"
        ).start(self)

    # ── FSM bar ────────────────────────────────────────────────

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
        anim = Animation(height=2, duration=0.15) + Animation(height=6, duration=0.15)
        anim.start(self._state_bar)

    # ── Navigation ─────────────────────────────────────────────

    def _go_to_insights(self, *_args: object) -> None:
        if self.manager is not None:
            self.manager.current = "insights"
