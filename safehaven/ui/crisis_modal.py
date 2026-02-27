"""Crisis resource popup — shown when RiskLevel is HIGH."""

from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from typing import Any


class CrisisModal(tk.Toplevel):
    """Modal dialog displaying crisis hotlines.

    Shown when the risk evaluator returns HIGH.  Locks the parent
    window's input until the user acknowledges with
    "I understand — continue chatting".
    """

    def __init__(self, parent: tk.Tk, on_dismiss: Any = None) -> None:
        super().__init__(parent)
        self._on_dismiss = on_dismiss

        self.title("We Care About You")
        self.resizable(False, False)
        self.configure(padx=20, pady=20)

        # Header
        header = tk.Label(
            self,
            text="We Care About You",
            font=("Helvetica", 16, "bold"),
            fg="#c0392b",
        )
        header.pack(pady=(0, 10))

        # Body
        body = tk.Label(
            self,
            text=(
                "It sounds like you may be in crisis.\n"
                "Please reach out to a professional:"
            ),
            font=("Helvetica", 11),
            wraplength=400,
            justify="center",
        )
        body.pack(pady=(0, 15))

        # Load and display hotlines
        hotlines_path = (
            Path(__file__).parent.parent / "resources" / "crisis_hotlines.json"
        )
        hotlines: dict[str, Any] = json.loads(
            hotlines_path.read_text(encoding="utf-8")
        )

        for region, info in hotlines.items():
            frame = tk.Frame(self, relief="groove", bd=1, padx=10, pady=6)
            frame.pack(fill="x", pady=3)

            label_text = f"{info['name']}"
            if region != "international":
                label_text = f"[{region.upper()}] {label_text}"

            name_label = tk.Label(
                frame,
                text=label_text,
                font=("Helvetica", 10, "bold"),
                anchor="w",
            )
            name_label.pack(anchor="w")

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
                detail_label = tk.Label(
                    frame,
                    text="\n".join(details),
                    font=("Helvetica", 9),
                    anchor="w",
                    justify="left",
                    fg="#555555",
                )
                detail_label.pack(anchor="w")

        # Dismiss button
        dismiss_btn = tk.Button(
            self,
            text="I understand \u2014 continue chatting",
            font=("Helvetica", 10),
            command=self._dismiss,
            bg="#2980b9",
            fg="white",
            padx=15,
            pady=5,
        )
        dismiss_btn.pack(pady=(15, 0))

        # Make truly modal
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._dismiss)

        # Center on parent
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_x()
        py = parent.winfo_y()
        w = self.winfo_width()
        h = self.winfo_height()
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.geometry(f"+{x}+{y}")

    def _dismiss(self) -> None:
        self.grab_release()
        self.destroy()
        if self._on_dismiss is not None:
            self._on_dismiss()
