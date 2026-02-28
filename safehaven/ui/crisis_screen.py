"""Kivy crisis screen — displays crisis resources and hotlines.

Replaces ``crisis_modal.py`` (Tkinter). Full-screen overlay with
crisis hotline information and acknowledgment button.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView

from safehaven.ui.theme import PRIMARY_COLOR, TEXT_COLOR, TEXT_SECONDARY


def _hex_to_rgba(hex_color: str) -> list[float]:
    """Convert a hex color string to Kivy RGBA (0–1 floats)."""
    h = hex_color.lstrip("#")
    return [int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4)] + [1.0]


class CrisisScreen(Screen):
    """Crisis resources screen — shown when RiskLevel is HIGH."""

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)

        with self.canvas.before:
            Color(1, 1, 1, 1)
            self._bg_rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_bg, pos=self._update_bg)

        root = BoxLayout(orientation="vertical", padding=20, spacing=12)

        # Header
        root.add_widget(
            Label(
                text="We Care About You",
                font_size="24sp",
                bold=True,
                color=[0.75, 0.22, 0.17, 1],  # #c0392b
                size_hint_y=None,
                height=40,
            )
        )

        # Body
        root.add_widget(
            Label(
                text=(
                    "It sounds like you may be in crisis.\n"
                    "Please reach out to a professional:"
                ),
                font_size="15sp",
                color=_hex_to_rgba(TEXT_COLOR),
                size_hint_y=None,
                height=50,
                halign="center",
            )
        )

        # Hotlines in a scroll view
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        hotline_list = BoxLayout(
            orientation="vertical", size_hint_y=None, spacing=10, padding=(10, 5)
        )
        hotline_list.bind(minimum_height=hotline_list.setter("height"))

        hotlines = self._load_hotlines()
        for region, info in hotlines.items():
            card = self._build_hotline_card(region, info)
            hotline_list.add_widget(card)

        scroll.add_widget(hotline_list)
        root.add_widget(scroll)

        # Dismiss button
        dismiss_btn = Button(
            text="I understand \u2014 continue chatting",
            font_size="15sp",
            size_hint=(0.7, None),
            height=48,
            pos_hint={"center_x": 0.5},
            background_color=_hex_to_rgba(PRIMARY_COLOR),
            color=[1, 1, 1, 1],
        )
        dismiss_btn.bind(on_release=self._dismiss)
        root.add_widget(dismiss_btn)

        self.add_widget(root)

    @staticmethod
    def _load_hotlines() -> dict[str, Any]:
        path = Path(__file__).parent.parent / "resources" / "crisis_hotlines.json"
        result: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        return result

    @staticmethod
    def _build_hotline_card(region: str, info: dict[str, Any]) -> BoxLayout:
        card = BoxLayout(orientation="vertical", size_hint_y=None, padding=10, spacing=4)

        # Region + name header
        label_text = info["name"]
        if region != "international":
            label_text = f"[{region.upper()}] {label_text}"

        card.add_widget(
            Label(
                text=label_text,
                font_size="14sp",
                bold=True,
                color=_hex_to_rgba(TEXT_COLOR),
                size_hint_y=None,
                height=24,
                halign="left",
            )
        )

        # Details
        details: list[str] = []
        phone: str | None = info.get("phone")
        text_line: str | None = info.get("text")
        url: str | None = info.get("url")
        if phone:
            details.append(f"Phone: {phone}")
        if text_line:
            details.append(text_line)
        if url:
            details.append(url)

        if details:
            card.add_widget(
                Label(
                    text="\n".join(details),
                    font_size="12sp",
                    color=_hex_to_rgba(TEXT_SECONDARY),
                    size_hint_y=None,
                    height=20 * len(details),
                    halign="left",
                )
            )

        card.height = sum(c.height for c in card.children) + 20
        return card

    def _dismiss(self, *_args: object) -> None:
        if self.manager is not None:
            # Notify chat screen that crisis was dismissed
            from safehaven.ui.chat_screen import ChatScreen

            chat = self.manager.get_screen("chat")
            assert isinstance(chat, ChatScreen)
            chat.on_crisis_dismissed()
            self.manager.current = "chat"

    def _update_bg(self, *_args: object) -> None:
        self._bg_rect.size = self.size
        self._bg_rect.pos = self.pos
