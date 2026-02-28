"""Kivy application entry point — manages screens and navigation.

Replaces the Tkinter-based UI. Uses ScreenManager for transitions between
welcome, chat, crisis, and insights screens.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager

from safehaven.ui.chat_screen import ChatScreen
from safehaven.ui.crisis_screen import CrisisScreen
from safehaven.ui.insights_screen import InsightsScreen
from safehaven.ui.welcome_screen import WelcomeScreen

if TYPE_CHECKING:
    from safehaven.controller.chat_controller import ChatController


class SafeHavenApp(App):
    """Main Kivy application with four-screen navigation."""

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._pending_controller: ChatController | None = None

    def build(self) -> ScreenManager:
        """Create the ScreenManager and register all screens."""
        self.title = "SafeHaven — Mental Health Chatbot"
        sm = ScreenManager()
        sm.add_widget(WelcomeScreen(name="welcome"))
        sm.add_widget(ChatScreen(name="chat"))
        sm.add_widget(CrisisScreen(name="crisis"))
        sm.add_widget(InsightsScreen(name="insights"))
        self._screen_manager = sm

        # Apply controller if set_controller() was called before build()
        if self._pending_controller is not None:
            chat_screen = sm.get_screen("chat")
            assert isinstance(chat_screen, ChatScreen)
            chat_screen.set_controller(self._pending_controller)

        return sm

    def set_controller(self, controller: ChatController) -> None:
        """Inject the ChatController into the chat screen (Observer pattern).

        Can be called before or after build().
        """
        self._pending_controller = controller
        # If build() already ran, apply immediately
        if hasattr(self, "_screen_manager"):
            chat_screen = self._screen_manager.get_screen("chat")
            assert isinstance(chat_screen, ChatScreen)
            chat_screen.set_controller(controller)
