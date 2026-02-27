"""Tkinter chat window — Presentation layer."""

from __future__ import annotations

import threading
import tkinter as tk
from typing import TYPE_CHECKING

from safehaven.ui.crisis_modal import CrisisModal

if TYPE_CHECKING:
    from safehaven.controller.chat_controller import ChatController


class ChatWindow(tk.Tk):
    """Main application window for SafeHaven.

    Uses the Observer pattern: the UI receives responses via a callback
    from the controller, decoupled from business logic.
    """

    def __init__(self) -> None:
        super().__init__()

        self.title("SafeHaven — Mental Health Chatbot")
        self.geometry("600x500")
        self.minsize(400, 350)

        self._controller: ChatController | None = None
        self._build_ui()

    def set_controller(self, controller: ChatController) -> None:
        """Inject the ChatController (Observer pattern)."""
        self._controller = controller

    # ── UI layout ──────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # Chat display
        display_frame = tk.Frame(self)
        display_frame.pack(fill="both", expand=True, padx=10, pady=(10, 5))

        self._scrollbar = tk.Scrollbar(display_frame)
        self._scrollbar.pack(side="right", fill="y")

        self._display = tk.Text(
            display_frame,
            wrap="word",
            state="disabled",
            font=("Helvetica", 11),
            yscrollcommand=self._scrollbar.set,
            bg="#f9f9f9",
            relief="sunken",
            bd=1,
        )
        self._display.pack(fill="both", expand=True)
        self._scrollbar.config(command=self._display.yview)

        # Tag styles for user vs assistant
        self._display.tag_configure("user", foreground="#2c3e50", font=("Helvetica", 11, "bold"))
        self._display.tag_configure("assistant", foreground="#2980b9")
        self._display.tag_configure("system", foreground="#7f8c8d", justify="center")

        # Input area
        input_frame = tk.Frame(self)
        input_frame.pack(fill="x", padx=10, pady=(0, 10))

        self._entry = tk.Entry(input_frame, font=("Helvetica", 11))
        self._entry.pack(side="left", fill="x", expand=True, ipady=4)
        self._entry.bind("<Return>", lambda _e: self._on_send())
        self._entry.focus_set()

        self._send_btn = tk.Button(
            input_frame,
            text="Send",
            font=("Helvetica", 10),
            command=self._on_send,
            padx=12,
        )
        self._send_btn.pack(side="right", padx=(6, 0))

        # Welcome message
        self._append_system("Welcome to SafeHaven. How are you feeling today?")

    # ── Interaction ────────────────────────────────────────────────

    def _on_send(self) -> None:
        text = self._entry.get().strip()
        if not text or self._controller is None:
            return

        self._entry.delete(0, "end")
        self._append_message("You", text, "user")
        self._set_input_enabled(False)

        # Run controller in background thread to keep UI responsive
        thread = threading.Thread(
            target=self._process_in_background, args=(text,), daemon=True
        )
        thread.start()

    def _process_in_background(self, text: str) -> None:
        assert self._controller is not None
        try:
            response = self._controller.handle_message(text)
        except Exception as exc:
            self.after(0, self._on_error, str(exc))
            return

        if response is None:
            # HIGH risk — show crisis modal on main thread
            self.after(0, self._show_crisis_modal)
        else:
            self.after(0, self._on_response, response)

    def _on_response(self, text: str) -> None:
        self._append_message("SafeHaven", text, "assistant")
        self._set_input_enabled(True)
        self._entry.focus_set()

    def _on_error(self, msg: str) -> None:
        self._append_system(f"[Error: {msg}]")
        self._set_input_enabled(True)
        self._entry.focus_set()

    def _show_crisis_modal(self) -> None:
        CrisisModal(self, on_dismiss=self._on_crisis_dismissed)

    def _on_crisis_dismissed(self) -> None:
        self._set_input_enabled(True)
        self._entry.focus_set()

    # ── Display helpers ────────────────────────────────────────────

    def _append_message(self, sender: str, text: str, tag: str) -> None:
        self._display.configure(state="normal")
        self._display.insert("end", f"{sender}: ", tag)
        self._display.insert("end", f"{text}\n\n")
        self._display.configure(state="disabled")
        self._display.see("end")

    def _append_system(self, text: str) -> None:
        self._display.configure(state="normal")
        self._display.insert("end", f"{text}\n\n", "system")
        self._display.configure(state="disabled")
        self._display.see("end")

    def _set_input_enabled(self, enabled: bool) -> None:
        if enabled:
            self._entry.configure(state="normal")
            self._send_btn.configure(state="normal")
        else:
            self._entry.configure(state="disabled")
            self._send_btn.configure(state="disabled")
