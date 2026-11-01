"""World Radio: cross-platform internet radio player using Tkinter and VLC."""
from __future__ import annotations

import json
import queue
import threading
import ctypes
import time
from concurrent.futures import ThreadPoolExecutor
import urllib.parse
import urllib.request
import tkinter as tk
from tkinter import messagebox, ttk
from pathlib import Path

try:
    import vlc
except ImportError:
    vlc = None

APP_DIR = Path(__file__).resolve().parent
FAVORITES_FILE = APP_DIR / "favorites.json"
API = "https://all.api.radio-browser.info/json"
HEADERS = {"User-Agent": "WorldRadioTk/1.0 (desktop player)"}
PAGE_SIZE = 200


def api_get(path: str, params: dict | None = None):
    url = API + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=18) as response:
        return json.loads(response.read().decode("utf-8"))


def station_id(s: dict) -> str:
    return s.get("stationuuid") or s.get("url_resolved") or s.get("url", "")


class WorldRadio(tk.Frame):
    BG = "#10151d"
    PANEL = "#171f2a"
    PANEL2 = "#202b38"
    TEXT = "#eef3f8"
    MUTED = "#96a5b5"
    GREEN = "#50d890"

    def __init__(self, master=None):
        self._owns_root = master is None
        if self._owns_root:
            master = tk.Tk()
            master.title("World Radio")
            master.geometry("1120x740")
            master.minsize(880, 600)
        super().__init__(master)
        self.root = self.winfo_toplevel()
        if self._owns_root:
            self.pack(fill="both", expand=True)
        self.configure(bg=self.BG)
        self.events: queue.Queue = queue.Queue()
        self.playback_events: queue.Queue = queue.Queue()
        self.stations: list[dict] = []
        self.offset = 0
        self.total_hint = None
        self.loading = False
        self.current = None
        self.active_media = None
        self._playback_lock = threading.Lock()
        self._playback_generation = 0
        self._playback_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="radio-vlc")
        self._volume_target = 75
        self._volume_applied = 75
        self._volume_job = None
        self.favorites = self.load_favorites()
        self.only_favorites = False
        self.remote_events = queue.Queue()
        self.remote_window_hooks = {}
        self.remote_key_state = {0xB0: False, 0xB1: False, 0xB2: False, 0xB3: False}
        self.last_remote_command = (None, 0.0)
        self.categories: list[str] = []
        self.countries: list[str] = []
        self._build_styles()
        self._build_ui()
        self.after(120, self._drain_events)
        self.after(350, self.load_directory)
        if vlc:
            try:
                # Apply stronger broadcast-style dynamic-range compression so
                # loud and quiet stations are closer in perceived level. Keep
                # the app slider as the final output-volume control.
                self.vlc_instance = vlc.Instance(
                    "--no-video", "--quiet", "--audio-filter=compressor,stereo_widen",
                    "--compressor-rms-peak=0.25", "--compressor-attack=20",
                    "--compressor-release=300", "--compressor-threshold=-24",
                    "--compressor-ratio=5", "--compressor-knee=8",
                    "--compressor-makeup-gain=6",
                    "--stereowiden-delay=20", "--stereowiden-feedback=0.25",
                    "--stereowiden-crossfeed=0.18", "--stereowiden-dry-mix=0.9")
                self.player = self.vlc_instance.media_player_new()
            except Exception as exc:
                self.vlc_instance = self.player = None
                self.set_status(f"VLC could not start: {exc}")
        else:
            self.vlc_instance = self.player = None
        if self._owns_root:
            self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.update_idletasks()
        self._install_remote_hook(self.root)
        self.after(100, self._poll_remote_controls)

    def _build_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview", background=self.PANEL, foreground=self.TEXT,
                        fieldbackground=self.PANEL, rowheight=34, borderwidth=0)
        style.configure("Treeview.Heading", background=self.PANEL2, foreground=self.MUTED,
                        font=("Segoe UI", 9, "bold"), relief="flat")
        style.map("Treeview", background=[("selected", "#28543f")],
                  foreground=[("selected", "white")])
        style.configure("TCombobox", fieldbackground=self.PANEL2, background=self.PANEL2,
                        foreground=self.TEXT, arrowcolor=self.TEXT)
        style.configure("Horizontal.TScale", background=self.PANEL)

    def _build_ui(self):
        header = tk.Frame(self, bg=self.BG)
        header.pack(fill="x", padx=26, pady=(22, 14))
        tk.Label(header, text="◉  WORLD RADIO", bg=self.BG, fg=self.TEXT,
                 font=("Segoe UI", 22, "bold")).pack(side="left")
        tk.Label(header, text="LIVE STATIONS  ·  AROUND THE WORLD", bg=self.BG,
                 fg=self.MUTED, font=("Segoe UI", 9, "bold")).pack(side="right", pady=10)

        controls = tk.Frame(self, bg=self.PANEL, padx=14, pady=12)
        controls.pack(fill="x", padx=24)
        self.search = tk.StringVar()
        search = tk.Entry(controls, textvariable=self.search, bg=self.PANEL2, fg=self.TEXT,
                          insertbackground=self.TEXT, relief="flat", font=("Segoe UI", 11))
        search.pack(side="left", fill="x", expand=True, ipady=9, padx=(0, 9))
        search.insert(0, "Search stations, countries, genres…")
        search.bind("<FocusIn>", lambda _e: self._clear_placeholder(search))
        search.bind("<Return>", lambda _e: self.search_directory())
        self._button(controls, "Search directory", self.search_directory, primary=True).pack(side="left", padx=4)
        self._button(controls, "Popular", self.load_directory).pack(side="left", padx=4)
        self._button(controls, "♥ Favorites", self.show_favorites).pack(side="left", padx=4)

        filters = tk.Frame(self, bg=self.BG)
        filters.pack(fill="x", padx=28, pady=(13, 8))
        tk.Label(filters, text="COUNTRY", bg=self.BG, fg=self.MUTED,
                 font=("Segoe UI", 8, "bold")).pack(side="left", padx=(0, 8))
        self.country_var = tk.StringVar(value="All countries")
        self.country_box = ttk.Combobox(filters, textvariable=self.country_var, state="readonly", width=23)
        self.country_box["values"] = ["All countries"]
        self.country_box.pack(side="left", padx=(0, 18))
        self.country_box.bind("<<ComboboxSelected>>", lambda _e: self.search_directory())
        tk.Label(filters, text="GENRE", bg=self.BG, fg=self.MUTED,
                 font=("Segoe UI", 8, "bold")).pack(side="left", padx=(0, 8))
        self.genre_var = tk.StringVar(value="All genres")
        self.genre_box = ttk.Combobox(filters, textvariable=self.genre_var, state="readonly", width=22)
        self.genre_box["values"] = ["All genres"]
        self.genre_box.pack(side="left", padx=(0, 18))
        self.genre_box.bind("<<ComboboxSelected>>", lambda _e: self.search_directory())
        self.sort_var = tk.StringVar(value="Popularity")
        ttk.Combobox(filters, textvariable=self.sort_var, state="readonly", width=15,
                     values=["Popularity", "Name A–Z", "Country A–Z"]).pack(side="left")
        self.sort_var.trace_add("write", lambda *_: self.render())
        self.count_label = tk.Label(filters, text="Connecting to station directory…", bg=self.BG,
                                    fg=self.MUTED, font=("Segoe UI", 9))
        self.count_label.pack(side="right")

        body = tk.Frame(self, bg=self.BG)
        body.pack(fill="both", expand=True, padx=24, pady=(2, 12))
        columns = ("name", "country", "genre", "codec", "bitrate", "votes")
        self.table = ttk.Treeview(body, columns=columns, show="headings", selectmode="browse")
        labels = {"name": "STATION", "country": "COUNTRY", "genre": "GENRE / TAGS",
                  "codec": "FORMAT", "bitrate": "KBPS", "votes": "POPULARITY"}
        widths = {"name": 330, "country": 175, "genre": 245, "codec": 90, "bitrate": 70, "votes": 95}
        for col in columns:
            self.table.heading(col, text=labels[col])
            self.table.column(col, width=widths[col], minwidth=55, anchor="w")
        self.table.column("bitrate", anchor="center")
        self.table.column("votes", anchor="center")
        scroll = ttk.Scrollbar(body, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scroll.set)
        self.table.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.table.bind("<Double-1>", lambda _e: self.play_selected())
        self.table.bind("<Return>", lambda _e: self.play_selected())
        self.table.bind("<space>", lambda _e: self.play_selected())

        foot = tk.Frame(self, bg=self.PANEL, padx=18, pady=13)
        foot.pack(fill="x", side="bottom")
        now = tk.Frame(foot, bg=self.PANEL)
        now.pack(side="left", fill="x", expand=True)
        self.now_title = tk.Label(now, text="Choose a station to start listening", bg=self.PANEL,
                                  fg=self.TEXT, font=("Segoe UI", 11, "bold"), anchor="w")
        self.now_title.pack(anchor="w")
        self.status = tk.Label(now, text="Directory powered by Radio Browser", bg=self.PANEL,
                               fg=self.MUTED, font=("Segoe UI", 9), anchor="w")
        self.status.pack(anchor="w", pady=(3, 0))
        actions = tk.Frame(foot, bg=self.PANEL)
        actions.pack(side="left", padx=18)
        self._button(actions, "▶  Play", self.play_selected, primary=True).pack(side="left", padx=3)
        self._button(actions, "Ⅱ  Pause", self.pause).pack(side="left", padx=3)
        self._button(actions, "■  Stop", self.stop).pack(side="left", padx=3)
        self._button(actions, "♥", self.toggle_favorite).pack(side="left", padx=3)
        self._button(actions, "◀ Fav", lambda: self.play_favorite_step(-1)).pack(side="left", padx=3)
        self._button(actions, "Fav ▶", lambda: self.play_favorite_step(1)).pack(side="left", padx=3)
        vol = tk.Frame(foot, bg=self.PANEL)
        vol.configure(width=315, height=34)
        vol.pack(side="right", padx=(12, 0))
        vol.pack_propagate(False)
        self.volume = tk.IntVar(value=75)
        tk.Label(vol, text="VOL", bg=self.PANEL, fg=self.MUTED,
                 font=("Segoe UI", 8, "bold")).pack(side="left", padx=(2, 7))
        self.volume_scale = tk.Scale(vol, from_=0, to=100, orient="horizontal",
            variable=self.volume, showvalue=False, resolution=1, length=220, width=5,
            sliderlength=15, bd=0, highlightthickness=0, relief="flat",
            bg=self.PANEL, fg=self.TEXT, troughcolor="#354653",
            activebackground="#79e1c2", command=self.set_volume)
        self.volume_scale.pack(side="left", fill="x", expand=True, padx=(0, 7))
        self.volume_bubble = tk.Label(vol, text="75%", width=4, bg="#293a49", fg=self.TEXT,
            font=("Segoe UI", 8, "bold"), padx=4, pady=3)
        self.volume_bubble.pack(side="right", padx=(0, 2))
        self._button(foot, "＋ Stream URL", self.add_stream_url).pack(side="right")
        self._button(foot, "Load more", self.load_more).pack(side="right", padx=8)

    def _button(self, parent, label, command, primary=False):
        return tk.Button(parent, text=label, command=command, bg="#278656" if primary else self.PANEL2,
                         activebackground="#39a96c" if primary else "#2b3948", fg=self.TEXT,
                         activeforeground=self.TEXT, relief="flat", bd=0, cursor="hand2",
                         padx=12, pady=8, font=("Segoe UI", 9, "bold" if primary else "normal"))

    def _clear_placeholder(self, entry):
        if entry.get().startswith("Search stations,"):
            entry.delete(0, "end")

    def load_favorites(self):
        try:
            return json.loads(FAVORITES_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

    def save_favorites(self):
        FAVORITES_FILE.write_text(json.dumps(self.favorites, ensure_ascii=False, indent=2), encoding="utf-8")

    def set_status(self, message):
        self.status.configure(text=message)

    def async_call(self, fn, on_success, message):
        if self.loading:
            return
        self.loading = True
        self.set_status(message)
        def run():
            try:
                self.events.put((on_success, fn(), None))
            except Exception as exc:
                self.events.put((on_success, None, str(exc)))
        threading.Thread(target=run, daemon=True).start()

    def _drain_events(self):
        try:
            while True:
                callback, result, error = self.events.get_nowait()
                self.loading = False
                if error:
                    self.set_status("Directory unavailable — check your internet connection and retry")
                    self.count_label.configure(text="Could not load stations")
                else:
                    callback(result)
        except queue.Empty:
            pass
        try:
            while True:
                result = self.playback_events.get_nowait()
                self._radio_stream_started(result)
        except queue.Empty:
            pass
        self.after(120, self._drain_events)

    def load_directory(self):
        self.only_favorites = False
        self.offset = 0
        self.async_call(lambda: api_get("/stations", {"limit": PAGE_SIZE, "offset": 0,
                         "order": "clickcount", "reverse": "true", "hidebroken": "true"}),
                        self._directory_loaded, "Loading popular stations…")
        self.load_filters()

    def load_filters(self):
        def fetch():
            countries = api_get("/countries", {"order": "stationcount", "reverse": "true", "hidebroken": "true"})
            tags = api_get("/tags", {"order": "stationcount", "reverse": "true", "limit": 120})
            return countries, tags
        def done(data):
            countries, tags = data
            self.countries = [x["name"] for x in countries if x.get("name")]
            self.categories = [x["name"] for x in tags if x.get("name")]
            self.country_box["values"] = ["All countries"] + self.countries
            self.genre_box["values"] = ["All genres"] + self.categories
        threading.Thread(target=lambda: self._safe_background(fetch, done), daemon=True).start()

    def _safe_background(self, fn, callback):
        try:
            self.events.put((callback, fn(), None))
        except Exception:
            pass

    def _directory_loaded(self, stations):
        self.stations = stations or []
        self.offset = len(self.stations)
        self.render()
        self.set_status("Choose a station and press Play, or double-click a row")

    def search_directory(self):
        self.only_favorites = False
        self.offset = 0
        term = self.search.get().strip()
        if term.startswith("Search stations,"):
            term = ""
        country = self.country_var.get()
        genre = self.genre_var.get()
        params = {"limit": PAGE_SIZE, "offset": 0, "order": "clickcount", "reverse": "true", "hidebroken": "true"}
        if term:
            params["name"] = term
        if country != "All countries":
            params["country"] = country
        if genre != "All genres":
            params["tag"] = genre
        self.async_call(lambda: api_get("/stations/search", params), self._directory_loaded,
                        "Searching the global station directory…")

    def load_more(self):
        if self.only_favorites or self.loading:
            return
        params = {"limit": PAGE_SIZE, "offset": self.offset, "order": "clickcount",
                  "reverse": "true", "hidebroken": "true"}
        term = self.search.get().strip()
        if term and not term.startswith("Search stations,"):
            params["name"] = term
        if self.country_var.get() != "All countries":
            params["country"] = self.country_var.get()
        if self.genre_var.get() != "All genres":
            params["tag"] = self.genre_var.get()
        self.async_call(lambda: api_get("/stations/search", params), self._more_loaded, "Loading more stations…")

    def _more_loaded(self, stations):
        known = {station_id(s) for s in self.stations}
        fresh = [s for s in stations if station_id(s) not in known]
        self.stations.extend(fresh)
        self.offset += len(stations)
        self.render()

    def show_favorites(self):
        self.only_favorites = True
        self.stations = list(self.favorites.values())
        self.render()
        self.set_status("Your saved stations")

    def render(self):
        rows = list(self.stations)
        sort = self.sort_var.get()
        if sort == "Name A–Z":
            rows.sort(key=lambda s: s.get("name", "").casefold())
        elif sort == "Country A–Z":
            rows.sort(key=lambda s: (s.get("country", "").casefold(), s.get("name", "").casefold()))
        else:
            rows.sort(key=lambda s: int(s.get("clickcount", 0) or 0), reverse=True)
        for item in self.table.get_children():
            self.table.delete(item)
        for s in rows:
            name = (s.get("name") or "Untitled station").strip()
            if station_id(s) == (station_id(self.current) if self.current else None):
                name = "▶  " + name
            self.table.insert("", "end", iid=str(hash(station_id(s))), values=(
                name, s.get("country", "") or "—", (s.get("tags", "") or "")[:42] or "—",
                (s.get("codec", "") or "—").upper(), s.get("bitrate", 0) or "—",
                s.get("clickcount", 0) or "—"))
        self._row_stations = {str(hash(station_id(s))): s for s in rows}
        self.count_label.configure(text=f"{len(rows):,} stations" + ("  ·  Favorites" if self.only_favorites else ""))

    def selected_station(self):
        selected = self.table.selection()
        if selected:
            return self._row_stations.get(selected[0])
        return None

    def play_selected(self):
        s = self.selected_station() or self.current
        if not s:
            self.set_status("Select a station from the list first")
            return
        url = s.get("url_resolved") or s.get("url")
        if not url:
            self.set_status("This station does not provide a stream URL")
            return
        if self.player is None:
            messagebox.showerror("Playback engine not found",
                "Install VLC media player and the Python VLC bindings.\n\n"
                "On Raspberry Pi OS, open Terminal and run:\n"
                "sudo apt install vlc python3-vlc python3-tk")
            return
        self._playback_generation += 1
        generation = self._playback_generation
        previous = self.current
        self.current = s
        station_name = (s.get("name") or "Internet radio").strip()
        station_country = (s.get("country") or "Online").strip()
        station_title = f"{station_name}  ·  {station_country}"
        self.now_title.configure(text=station_title)
        if hasattr(self, "station_header_title"):
            self.station_header_title.configure(text=station_title)
        self.set_status("Connecting to live stream…  ·  " + (s.get("country") or "Online"))
        self._update_playing_rows(previous, s)
        volume = self.volume.get()
        self._playback_executor.submit(self._open_radio_stream, generation, url, volume)

    def _update_playing_rows(self, previous_station, playing_station):
        """Update only the affected rows instead of rebuilding the full list."""
        stations = {station_id(s): s for s in (previous_station, playing_station) if s}
        for key, station in stations.items():
            iid = str(hash(key))
            if not self.table.exists(iid):
                continue
            values = list(self.table.item(iid, "values"))
            if values:
                name = (station.get("name") or "Untitled station").strip()
                values[0] = ("▶  " if key == station_id(playing_station) else "") + name
                self.table.item(iid, values=values)

    def _open_radio_stream(self, generation, url, volume):
        """Open/replace a radio stream off Tk's UI thread."""
        error = None
        new_media = None
        try:
            with self._playback_lock:
                if generation != self._playback_generation:
                    return
                self.player.stop()
                self._release_active_media(clear_player=True)
                if generation != self._playback_generation:
                    return
                new_media = self.vlc_instance.media_new(url)
                new_media.add_option(":http-user-agent=Mozilla/5.0 WorldRadio/1.0")
                self.player.set_media(new_media)
                self.active_media = new_media
                self.player.audio_set_volume(volume)
                self.player.play()
                self.player.audio_set_mute(False)
                self.player.audio_set_volume(volume)
        except Exception as exc:
            error = str(exc)
            if new_media is not None and self.active_media is not new_media:
                try:
                    new_media.release()
                except Exception:
                    pass
        self.playback_events.put((generation, error))

    def _radio_stream_started(self, result):
        generation, error = result
        if generation != self._playback_generation or not self.winfo_exists():
            return
        if error:
            self.set_status(f"Could not start stream: {error}")
            return
        self.set_status("Connecting to live stream…")
        # Some VLC outputs initialize after play() returns. Reapply the chosen
        # level once that output has had time to come up.
        self.after(450, lambda g=generation: self._restore_radio_audio(g))
        self.after(1300, lambda g=generation: self._restore_radio_audio(g))
        self.after(1800, self._check_playback)

    def _restore_radio_audio(self, generation):
        if generation != self._playback_generation or not self.player:
            return
        level = max(0, min(100, int(self.volume.get())))
        try:
            self.player.audio_set_volume(level)
            self.player.audio_set_mute(level == 0)
        except Exception:
            pass

    def _check_playback(self):
        if self.player and self.current and self.player.get_state() == vlc.State.Error:
            self.set_status("Stream failed — try another station or retry")
        elif self.player and self.current and self.player.is_playing():
            self.set_status("LIVE  ·  " + (self.current.get("country") or "Online"))

    def pause(self):
        if self.player:
            try:
                self.player.set_pause(1)
            except Exception:
                self.player.pause()
            self.set_status("Playback paused")

    def resume(self):
        if self.player and self.current:
            try:
                self.player.audio_set_mute(False)
                self.player.audio_set_volume(self.volume.get())
                state = self.player.get_state()
                if state == vlc.State.Paused:
                    self.player.set_pause(0)
                    self.set_status("Playback resumed")
                    return
                if state in (vlc.State.Opening, vlc.State.Buffering, vlc.State.Playing):
                    self.set_status("Radio stream is already connecting or playing")
                    return
            except Exception:
                pass
            self._play_radio_station(self.current)
        elif self.favorites:
            self._play_radio_station(next(iter(self.favorites.values())))
        else:
            self.set_status("Save a station as a favorite, then press Play")

    def toggle_play_pause(self):
        if self.player and self.current:
            try:
                state = self.player.get_state()
                if state == vlc.State.Playing:
                    self.pause()
                    return
                if state == vlc.State.Paused:
                    self.resume()
                    return
                if state in (vlc.State.Opening, vlc.State.Buffering):
                    self.set_status("Radio stream is still connecting")
                    return
            except Exception:
                pass
        self.resume()

    def play_favorite_step(self, direction):
        favorites = list(self.favorites.values())
        if not favorites:
            self.set_status("Save stations as favorites to use next/previous")
            return
        favorite_ids = [station_id(station) for station in favorites]
        current_id = station_id(self.current) if self.current else None
        if current_id not in favorite_ids:
            index = 0 if direction > 0 else len(favorites) - 1
        else:
            index = (favorite_ids.index(current_id) + direction) % len(favorites)
        self._play_radio_station(favorites[index])
        self.set_status(f"Favorite {index + 1} of {len(favorites)} · {favorites[index].get('name', 'Radio')}")

    def _play_radio_station(self, station):
        self.current = station
        try:
            selection = self.table.selection()
            if selection:
                self.table.selection_remove(*selection)
            iid = str(hash(station_id(station)))
            if iid in self._row_stations:
                self.table.selection_set(iid)
            self.play_selected()
        except tk.TclError:
            self.play_selected()

    def _install_remote_hook(self, window):
        """Queue Windows Bluetooth/media remote commands for the UI thread."""
        try:
            hwnd = int(window.winfo_id())
            if hwnd in self.remote_window_hooks:
                return
            user32 = ctypes.windll.user32
            set_proc = getattr(user32, "SetWindowLongPtrW", None) or user32.SetWindowLongW
            set_proc.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
            set_proc.restype = ctypes.c_void_p
            call_proc = user32.CallWindowProcW
            call_proc.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint,
                                  ctypes.c_size_t, ctypes.c_ssize_t]
            call_proc.restype = ctypes.c_ssize_t
            old_proc = ctypes.c_void_p()
            app = self

            @ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_void_p, ctypes.c_uint,
                                ctypes.c_size_t, ctypes.c_ssize_t)
            def window_proc(h_wnd, message, w_param, l_param):
                if message == 0x0319:  # WM_APPCOMMAND
                    command = (int(l_param) >> 16) & 0x0FFF
                    if command in (11, 12, 13, 14, 46, 47):
                        app.remote_events.put(command)
                        return 1
                return call_proc(old_proc, h_wnd, message, w_param, l_param)

            old_proc = set_proc(hwnd, -4, ctypes.cast(window_proc, ctypes.c_void_p))
            if old_proc:
                self.remote_window_hooks[hwnd] = (window_proc, old_proc)
        except Exception:
            return

    def _poll_remote_controls(self):
        if not self.winfo_exists():
            return
        mapped = bool(self.winfo_ismapped())
        app_active = False
        try:
            user32 = ctypes.windll.user32
            user32.GetForegroundWindow.restype = ctypes.c_void_p
            user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
            user32.GetAsyncKeyState.restype = ctypes.c_short
            user32.IsChild.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
            user32.IsChild.restype = ctypes.c_bool
            active = user32.GetForegroundWindow() or 0
            root_hwnd = self.root.winfo_id()
            app_active = active == root_hwnd or user32.IsChild(root_hwnd, active)
            for key in self.remote_key_state:
                down = bool(user32.GetAsyncKeyState(key) & 0x8000)
                if mapped and app_active and down and not self.remote_key_state[key]:
                    self._handle_remote_command({0xB0: 11, 0xB1: 12, 0xB2: 13, 0xB3: 14}[key])
                self.remote_key_state[key] = down
        except Exception:
            pass
        try:
            while True:
                command = self.remote_events.get_nowait()
                if mapped:
                    self._handle_remote_command(command)
                elif getattr(self.root, "active_mode", None) == "tv":
                    self.root.tv._handle_appcommand(command)
        except queue.Empty:
            pass
        if self.winfo_exists():
            self.after(100, self._poll_remote_controls)

    def _handle_remote_command(self, command):
        now = time.monotonic()
        previous, previous_time = self.last_remote_command
        if previous == command and now - previous_time < 0.22:
            return
        self.last_remote_command = (command, now)
        if command == 11:
            self.play_favorite_step(1)
        elif command == 12:
            self.play_favorite_step(-1)
        elif command == 14:
            self.toggle_play_pause()
        elif command == 46:
            self.resume()
        elif command == 47:
            self.pause()
        elif command == 13:
            self.stop()

    def stop(self):
        if self.player:
            self._playback_generation += 1
            generation = self._playback_generation
            player = self.player
            media, self.active_media = self.active_media, None
            self._playback_executor.submit(self._stop_radio_stream, generation, player, media)
        self.set_status("Playback stopped")

    def _stop_radio_stream(self, generation, player, media):
        with self._playback_lock:
            if generation == self._playback_generation:
                try:
                    player.stop()
                except Exception:
                    pass
                try:
                    player.set_media(None)
                except Exception:
                    pass
            if media is not None:
                try:
                    media.release()
                except Exception:
                    pass

    def _release_active_media(self, clear_player=False):
        media, self.active_media = self.active_media, None
        if clear_player and self.player:
            try:
                self.player.set_media(None)
            except Exception:
                pass
        if media is not None:
            try:
                media.release()
            except Exception:
                pass

    def set_volume(self, value):
        level = max(0, min(100, int(round(float(value)))))
        self._volume_target = level
        if hasattr(self, "volume_bubble"):
            self.volume_bubble.configure(text=f"{level}%")
        if level > 0 and self.player:
            try:
                self.player.audio_set_mute(False)
            except Exception:
                pass
        if self._volume_job is None:
            self._ramp_volume()

    def _ramp_volume(self):
        self._volume_job = None
        target = self._volume_target
        current = self._volume_applied
        difference = target - current
        if difference:
            step = max(1, (abs(difference) + 7) // 8)
            current += step if difference > 0 else -step
            self._volume_applied = current
            if self.player:
                try:
                    self.player.audio_set_volume(current)
                    self.player.audio_set_mute(current == 0)
                except Exception as exc:
                    self.set_status(f"Could not change audio volume: {exc}")
        if self._volume_applied != self._volume_target:
            self._volume_job = self.after(18, self._ramp_volume)

    def toggle_favorite(self):
        s = self.selected_station() or self.current
        if not s:
            return
        key = station_id(s)
        if key in self.favorites:
            del self.favorites[key]
            self.set_status("Removed from favorites")
        else:
            self.favorites[key] = s
            self.set_status("Saved to favorites")
        self.save_favorites()
        if self.only_favorites:
            self.show_favorites()

    def add_stream_url(self):
        dialog = tk.Toplevel(self)
        dialog.title("Add a radio station")
        dialog.configure(bg=self.PANEL)
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        tk.Label(dialog, text="Add a station by name and stream address", bg=self.PANEL,
                 fg=self.TEXT, font=("Segoe UI", 10)).pack(anchor="w", padx=18, pady=(18, 8))
        name_var = tk.StringVar(value="My radio station")
        url_var = tk.StringVar()
        tk.Label(dialog, text="Station name (shown in the list)", bg=self.PANEL,
                 fg=self.MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=18, pady=(6, 2))
        name_entry = tk.Entry(dialog, textvariable=name_var, width=55, font=("Segoe UI", 10))
        name_entry.pack(padx=18, pady=(0, 8), ipady=5)
        tk.Label(dialog, text="Direct stream URL", bg=self.PANEL,
                 fg=self.MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=18, pady=(2, 2))
        url_entry = tk.Entry(dialog, textvariable=url_var, width=55, font=("Segoe UI", 10))
        url_entry.pack(padx=18, pady=(0, 5), ipady=5)
        def add():
            name = name_var.get().strip()
            url = url_var.get().strip()
            if not url.startswith(("http://", "https://")):
                messagebox.showerror("Invalid URL", "Enter a URL beginning with http:// or https://", parent=dialog)
                return
            if not name or name.lower().startswith(("http://", "https://")):
                messagebox.showerror("Station name required",
                    "Enter the station name in the Station name box. Put the stream address in the URL box.",
                    parent=dialog)
                name_entry.focus_set()
                return
            s = {"stationuuid": url, "name": name,
                 "url": url, "url_resolved": url, "country": "Custom", "tags": "Added by you",
                 "codec": "", "bitrate": 0, "clickcount": 0}
            self.current = s
            self.play_selected_custom(s)
            dialog.destroy()
        buttons = tk.Frame(dialog, bg=self.PANEL)
        buttons.pack(fill="x", padx=18, pady=16)
        self._button(buttons, "Play stream", add, primary=True).pack(side="right")
        self._button(buttons, "Cancel", dialog.destroy).pack(side="right", padx=8)
        name_entry.focus_set()
        name_entry.selection_range(0, "end")

    def play_selected_custom(self, s):
        self.stations.append(s)
        self.render()
        iid = str(hash(station_id(s)))
        if iid in self._row_stations:
            self.table.selection_set(iid)
        self.play_selected()

    def close(self):
        self._playback_generation += 1
        try:
            self._remove_remote_hook(self.root)

            def release_player():
                with self._playback_lock:
                    media, self.active_media = self.active_media, None
                if self.player:
                    try:
                        self.player.audio_set_mute(True)
                    except Exception:
                        pass
                    try:
                        self.player.stop()
                    except Exception:
                        pass
                    try:
                        self.player.set_media(None)
                    except Exception:
                        pass
                if media is not None:
                    try:
                        media.release()
                    except Exception:
                        pass
                if self.vlc_instance:
                    self.vlc_instance.release()

            self._playback_executor.submit(release_player)
            self._playback_executor.shutdown(wait=False, cancel_futures=False)
        finally:
            self.destroy()
            if self._owns_root:
                self.root.destroy()

    def _remove_remote_hook(self, window):
        try:
            hwnd = int(window.winfo_id())
            entry = self.remote_window_hooks.pop(hwnd, None)
            if not entry:
                return
            _callback, old_proc = entry
            user32 = ctypes.windll.user32
            set_proc = getattr(user32, "SetWindowLongPtrW", None) or user32.SetWindowLongW
            set_proc.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
            set_proc.restype = ctypes.c_void_p
            set_proc(hwnd, -4, old_proc)
        except Exception:
            pass


if __name__ == "__main__":
    app = WorldRadio()
    app.root.mainloop()
