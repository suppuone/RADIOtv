"""Full SURAK Media Center edition for Raspberry Pi 5 and Linux."""
from __future__ import annotations

import os
import json
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from urllib.request import Request, urlopen


GITHUB_COMMIT_URL = "https://api.github.com/repos/suppuone/RADIOtv/commits/main"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/suppuone/RADIOtv"
UPDATE_FILES = (
    "media_center_linux_pi5.py",
    "radio_app.py",
    "radio_map_windows.py",
    "live_tv_windows.py",
    "magazine_reader.py",
    "countries.geojson",
)

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
        self._update_events = queue.Queue()
        self._update_busy = False
        self._pending_restart = False

        bar = tk.Frame(self, bg=self.PANEL, padx=16, pady=9)
        bar.pack(fill="x")
        tk.Label(bar, text="SURAK MEDIA CENTER", bg=self.PANEL, fg=self.TEXT,
                 font=("DejaVu Sans", 14, "bold")).pack(side="left")
        self.update_button = tk.Button(
            bar, text="↻ CHECK UPDATES", command=self._update_button_clicked,
            bg="#202b38", fg=self.TEXT, activebackground="#315b49",
            activeforeground=self.TEXT, relief="flat", bd=0, cursor="hand2",
            padx=12, pady=9, font=("DejaVu Sans", 9, "bold"))
        self.update_button.pack(side="right", padx=(7, 0))
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

    def _update_button_clicked(self):
        if self._pending_restart:
            self._restart_with_updated_files()
            return
        if self._update_busy:
            return
        self._update_busy = True
        self.update_button.configure(text="CHECKING…", state="disabled")
        threading.Thread(target=self._download_latest_version, daemon=True).start()
        self.after(120, self._poll_update_result)

    @staticmethod
    def _read_url(url, limit):
        request = Request(url, headers={
            "User-Agent": "SURAKMediaCenter-Pi5/1.0",
            "Accept": "application/json, text/plain, */*",
        })
        with urlopen(request, timeout=25) as response:
            content = response.read(limit + 1)
        if len(content) > limit:
            raise ValueError("The update file is larger than expected.")
        return content

    def _download_latest_version(self):
        app_dir = Path(__file__).resolve().parent
        staging_root = None
        try:
            metadata = json.loads(self._read_url(GITHUB_COMMIT_URL, 256_000).decode("utf-8"))
            commit = str(metadata.get("sha", ""))
            if len(commit) != 40 or any(char not in "0123456789abcdef" for char in commit.lower()):
                raise ValueError("GitHub returned an invalid version number.")

            version_file = app_dir / ".github_update_sha"
            try:
                installed_commit = version_file.read_text(encoding="ascii").strip()
            except OSError:
                installed_commit = ""
            if installed_commit == commit:
                self._update_events.put(("current", None))
                return

            staging_root = Path(tempfile.mkdtemp(prefix=".radio-update-", dir=str(app_dir)))
            staged_dir = staging_root / "new"
            backup_dir = staging_root / "backup"
            staged_dir.mkdir()
            backup_dir.mkdir()
            for name in UPDATE_FILES:
                url = f"{GITHUB_RAW_BASE}/{commit}/{name}"
                data = self._read_url(url, 12_000_000)
                data.decode("utf-8")  # reject incomplete or unexpected binary content
                (staged_dir / name).write_bytes(data)

            replaced = []
            try:
                for name in UPDATE_FILES:
                    destination = app_dir / name
                    backup = backup_dir / name
                    if destination.exists():
                        shutil.copy2(destination, backup)
                    os.replace(staged_dir / name, destination)
                    replaced.append(name)
                marker_temp = staging_root / "version"
                marker_temp.write_text(commit + "\n", encoding="ascii")
                os.replace(marker_temp, version_file)
            except Exception:
                for name in reversed(replaced):
                    destination = app_dir / name
                    backup = backup_dir / name
                    if backup.exists():
                        os.replace(backup, destination)
                    else:
                        destination.unlink(missing_ok=True)
                raise
            self._update_events.put(("updated", commit))
        except Exception as exc:
            self._update_events.put(("error", str(exc)))
        finally:
            if staging_root:
                shutil.rmtree(staging_root, ignore_errors=True)

    def _poll_update_result(self):
        if not self.winfo_exists():
            return
        try:
            kind, detail = self._update_events.get_nowait()
        except queue.Empty:
            self.after(120, self._poll_update_result)
            return
        self._update_busy = False
        self.update_button.configure(state="normal")
        if kind == "current":
            self.update_button.configure(text="✓ UP TO DATE")
            messagebox.showinfo("CoolMag Media Center", "You already have the latest version.", parent=self)
        elif kind == "updated":
            self._pending_restart = True
            self.update_button.configure(text="↻ RESTART TO APPLY", bg="#278656")
            if messagebox.askyesno(
                    "Update ready",
                    "The latest files were downloaded. Restart the media center now to apply them?",
                    parent=self):
                self._restart_with_updated_files()
        else:
            self.update_button.configure(text="↻ CHECK UPDATES")
            messagebox.showerror(
                "Update failed",
                f"Could not download the update from GitHub.\n\n{detail}\n\n"
                "Check the Wi-Fi connection and try again.", parent=self)

    def _restart_with_updated_files(self):
        script = Path(__file__).resolve()
        self.close()
        subprocess.Popen(
            [sys.executable, str(script)], cwd=str(script.parent),
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, close_fds=True, start_new_session=True)

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

