"""Full SURAK Media Center edition for Raspberry Pi 5 and Linux."""
from __future__ import annotations

import os
import tkinter as tk

# Select the full interface in the shared feature panels (map, tickers, TV cards).
os.environ["SURAK_PI_LITE"] = "0"


class SurakMediaCenterPi5(tk.Tk):
    BG = "#0b1118"
    PANEL = "#141e28"
    TEXT = "#eef5f4"

    def __init__(self):
        super().__init__()
        self.title("SURAK MEDIA CENTER")
        screen_width, screen_height = self.winfo_screenwidth(), self.winfo_screenheight()
        width = min(1440, max(900, screen_width - 30))
        height = min(900, max(600, screen_height - 80))
        self.geometry(f"{width}x{height}")
        self.minsize(min(900, width), min(600, height))
        self.configure(bg=self.BG)
        self.active_mode = None
        self.panels = {}

        bar = tk.Frame(self, bg=self.PANEL, padx=16, pady=9)
        bar.pack(fill="x")
        tk.Label(bar, text="SURAK MEDIA CENTER", bg=self.PANEL, fg=self.TEXT,
                 font=("DejaVu Sans", 14, "bold")).pack(side="left")
        self.radio_button = self._mode_button(bar, "◉  RADIO MAP", "radio")
        self.tv_button = self._mode_button(bar, "▣  LIVE TV", "tv")
        self.news_button = self._mode_button(bar, "▤  NEWS & MAGAZINES", "news")
        self.news_button.pack(side="right", padx=(7, 0))
        self.tv_button.pack(side="right", padx=(7, 0))
        self.radio_button.pack(side="right")

        self.content = tk.Frame(self, bg=self.BG)
        self.content.pack(fill="both", expand=True)
        self.radio = self.tv = self.news = None

        # Support common Bluetooth speaker remotes on Raspberry Pi OS.
        for keysym, action in (("XF86AudioNext", "next"), ("XF86AudioPrev", "previous"),
                               ("XF86AudioPlay", "play"), ("XF86AudioPause", "pause"),
                               ("XF86AudioStop", "stop")):
            self.bind_all(f"<{keysym}>", lambda _event, a=action: self._media_key(a))
        self.bind_all("<F11>", self._fullscreen_key)
        self.bind_all("<Escape>", self._escape_key)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.switch_mode("radio")
        self._update_buttons()

    def _mode_button(self, parent, text, mode):
        return tk.Button(parent, text=text, command=lambda: self.switch_mode(mode),
                         bg="#244337", fg=self.TEXT, activebackground="#315b49",
                         activeforeground=self.TEXT, relief="flat", bd=0, cursor="hand2",
                         padx=13, pady=9, font=("DejaVu Sans", 9, "bold"))

    def _update_buttons(self):
        for mode, button in (("radio", self.radio_button), ("tv", self.tv_button),
                             ("news", self.news_button)):
            button.configure(bg="#278656" if mode == self.active_mode else "#202b38")

    def switch_mode(self, mode):
        if mode == self.active_mode:
            return
        old = self.panels.get(self.active_mode)
        if old is not None:
            old.suspend_view()
            old.pack_forget()
        panel = self.panels.get(mode)
        if panel is None:
            if mode == "radio":
                from radio_map_windows import WorldRadioMap
                panel = WorldRadioMap(self.content)
            elif mode == "tv":
                from live_tv_windows import LiveTV
                panel = LiveTV(self.content)
            else:
                from magazine_reader import MagazineReader
                panel = MagazineReader(self.content)
            self.panels[mode] = panel
            setattr(self, mode, panel)
        else:
            panel.resume_view()
        panel.pack(fill="both", expand=True)
        self.active_mode = mode
        self._update_buttons()

    def _media_key(self, action):
        if self.active_mode not in ("radio", "tv"):
            return "break"
        panel = self.panels.get(self.active_mode)
        if panel is None:
            return "break"
        if action == "next":
            panel.play_favorite_step(1)
        elif action == "previous":
            panel.play_favorite_step(-1)
        elif action in ("play", "pause"):
            panel.toggle_play_pause()
        elif action == "stop":
            panel.stop()
        return "break"

    def _fullscreen_key(self, _event=None):
        if self.active_mode == "tv":
            self.tv.toggle_fullscreen()
            return "break"

    def _escape_key(self, _event=None):
        if self.active_mode == "tv" and self.tv.fullscreen:
            self.tv._leave_fullscreen()
            return "break"

    def close(self):
        for panel in tuple(self.panels.values()):
            try:
                panel.close()
            except Exception:
                pass
        self.destroy()


if __name__ == "__main__":
    SurakMediaCenterPi5().mainloop()
