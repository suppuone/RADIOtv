"""Simple Windows live TV player with VLC and M3U playlist support."""
from __future__ import annotations

import queue
import re
import json
import ctypes
import time
import base64
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
import threading
import sys
import os
import urllib.request
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

try:
    import vlc
except ImportError:
    vlc = None

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = ImageTk = None

FREE_TV_GUIDE = "https://iptv-org.github.io/iptv/index.m3u"
PLAYLIST_PRESETS = {
    "All channels": FREE_TV_GUIDE,
    "Free-TV (curated)": "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8",
    "Public IPTV (community)": "https://raw.githubusercontent.com/freecasthub/public-iptv/main/playlist.m3u",
    "India": "https://iptv-org.github.io/iptv/countries/in.m3u",
    "Singapore": "https://iptv-org.github.io/iptv/countries/sg.m3u",
    "Asia": "https://iptv-org.github.io/iptv/regions/asia.m3u",
    "Southeast Asia": "https://iptv-org.github.io/iptv/regions/asean.m3u",
    "News": "https://iptv-org.github.io/iptv/categories/news.m3u",
    "Sports": "https://iptv-org.github.io/iptv/categories/sports.m3u",
    "Movies": "https://iptv-org.github.io/iptv/categories/movies.m3u",
    "Kids": "https://iptv-org.github.io/iptv/categories/kids.m3u",
    "English": "https://iptv-org.github.io/iptv/languages/eng.m3u",
    "Hindi": "https://iptv-org.github.io/iptv/languages/hin.m3u",
    "Tamil": "https://iptv-org.github.io/iptv/languages/tam.m3u",
    "Nepali": "https://iptv-org.github.io/iptv/languages/nep.m3u",
}
APP_DIR = Path(__file__).resolve().parent
FAVORITES_FILE = APP_DIR / "surak_home_tv_favorites.json"


def parse_m3u(text: str) -> list[dict]:
    """Read standard M3U/EXTINF entries, retaining per-channel VLC options."""
    channels = []
    pending = None
    options = []
    for raw in text.replace("\r", "").split("\n"):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#EXTINF:"):
            details = line.split(",", 1)
            title = details[1].strip() if len(details) > 1 else "Untitled channel"
            attrs = dict(re.findall(r'([\w-]+)="([^"]*)"', details[0]))
            pending = {"name": attrs.get("tvg-name") or title,
                       "group": attrs.get("group-title", "TV"),
                       "logo": attrs.get("tvg-logo", "")}
            options = []
        elif line.startswith("#EXTVLCOPT:") and pending is not None:
            options.append(line.split(":", 1)[1].strip())
        elif line.startswith("#EXTGRP:") and pending is not None:
            pending["group"] = line.partition(":")[2].strip()
        elif line.startswith("#"):
            continue
        elif pending is not None and line.lower().startswith(("http://", "https://", "rtmp://", "rtsp://")):
            pending["url"] = line
            pending["options"] = options[:]
            channels.append(pending)
            pending = None
            options = []
    return channels


class LiveTV(tk.Frame):
    BG = "#10151d"
    PANEL = "#171f2a"
    PANEL2 = "#202b38"
    TEXT = "#eef3f8"
    MUTED = "#96a5b5"
    GREEN = "#50d890"

    def __init__(self, master=None):
        self._pi_lite_tv = os.environ.get("SURAK_PI_LITE") == "1"
        self._owns_root = master is None
        if self._owns_root:
            master = tk.Tk()
            master.title("SURAK HOME TV")
            master.geometry("1180x750")
            master.minsize(900, 600)
        super().__init__(master)
        self.root = self.winfo_toplevel()
        if self._owns_root:
            self.pack(fill="both", expand=True)
        self.configure(bg=self.BG)
        self.events: queue.Queue = queue.Queue()
        self.channels: list[dict] = []
        self.visible_channels: list[dict] = []
        self.selected_channel_data: dict | None = None
        self.card_batch_size = 24 if os.environ.get("SURAK_PI_LITE") == "1" else 48
        self.card_limit = self.card_batch_size
        self.logo_events: queue.Queue = queue.Queue()
        self.logo_pending: set[str] = set()
        self.logo_images: dict[str, tk.PhotoImage] = {}
        self.logo_labels: dict[str, list[tk.Label]] = {}
        logo_workers = 2 if os.environ.get("SURAK_PI_LITE") == "1" else 6
        self.logo_executor = ThreadPoolExecutor(max_workers=logo_workers, thread_name_prefix="tv-logo")
        self.playback_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="tv-playback")
        self.playback_generation = 0
        self.current: dict | None = None
        self.active_media = None
        self.favorites = self._load_favorites()
        self.showing_favorites = False
        self.fullscreen = False
        self.fullscreen_window = None
        self.fullscreen_video = None
        self.fullscreen_title_label = None
        self._f11_down = False
        self._escape_down = False
        self._media_next_down = False
        self._media_previous_down = False
        self._media_play_pause_down = False
        self._media_stop_down = False
        self.appcommand_events = queue.Queue()
        self._wndproc_hooks = {}
        self._last_media_command = (None, 0.0)
        self.aspect_modes = [("Auto", None), ("16:9", b"16:9"), ("4:3", b"4:3")]
        self.aspect_index = 0
        self._video_fit_job = None
        self.loading = False
        self._view_suspended = False
        self._volume_target = 75
        self._volume_applied = 75
        self._volume_job = None
        self._build_styles()
        self._build_ui()
        self._init_player()
        self.update_idletasks()
        self._install_appcommand_hook(self)
        self._install_appcommand_hook(self.video_surface)
        self.after(140, self._drain_events)
        self.after(100, self._poll_fullscreen_hotkeys)
        # Favorites are local, but the main channel list comes from the online guide.
        # Load it automatically so Home is populated on first launch.
        self.after(350, self.load_public_guide)
        if self._owns_root:
            self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _load_favorites(self):
        try:
            data = json.loads(FAVORITES_FILE.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def _save_favorites(self):
        try:
            FAVORITES_FILE.write_text(json.dumps(self.favorites, ensure_ascii=False, indent=2),
                                      encoding="utf-8")
        except OSError as exc:
            self.status.configure(text=f"Could not save favorites: {exc}")

    def _build_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview", background=self.PANEL, foreground=self.TEXT,
                        fieldbackground=self.PANEL, rowheight=31, borderwidth=0)
        style.configure("Treeview.Heading", background=self.PANEL2, foreground=self.MUTED,
                        font=("Segoe UI", 9, "bold"), relief="flat")
        style.map("Treeview", background=[("selected", "#28543f")],
                  foreground=[("selected", "white")])
        style.configure("Horizontal.TScale", background=self.PANEL)

    def _build_ui(self):
        header = tk.Frame(self, bg=self.BG)
        header.pack(fill="x", padx=22, pady=(18, 12))
        tk.Label(header, text="▣  SURAK HOME TV", bg=self.BG, fg=self.TEXT,
                 font=("Segoe UI", 22, "bold")).pack(side="left")
        nav = tk.Frame(header, bg=self.BG)
        nav.pack(side="right")
        self._button(nav, "⌂  HOME", self.show_home).pack(side="left", padx=3)
        self._button(nav, "▶  WATCH", self.show_watch).pack(side="left", padx=3)

        source = tk.Frame(self, bg=self.PANEL, padx=11, pady=10)
        source.pack(fill="x", padx=20)
        self.playlist_url = tk.StringVar(value=FREE_TV_GUIDE)
        self.playlist_preset = tk.StringVar(value="All channels")
        preset_box = ttk.Combobox(source, textvariable=self.playlist_preset,
                                  values=list(PLAYLIST_PRESETS), state="readonly", width=17)
        preset_box.pack(side="left", padx=(0, 7), ipady=5)
        preset_box.bind("<<ComboboxSelected>>", self._select_playlist_preset)
        url_entry = tk.Entry(source, textvariable=self.playlist_url, bg=self.PANEL2, fg=self.TEXT,
                             insertbackground=self.TEXT, relief="flat", font=("Segoe UI", 9))
        url_entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 7))
        url_entry.bind("<Return>", lambda _e: self.load_playlist_url())
        self._button(source, "Load selection", self.load_selected_preset, primary=True).pack(side="left", padx=3)
        self._button(source, "Load URL", self.load_playlist_url).pack(side="left", padx=3)
        self._button(source, "Open M3U file…", self.open_playlist_file).pack(side="left", padx=3)
        self.status = tk.Label(source, text="Load a guide to browse channels", bg=self.PANEL,
                               fg=self.MUTED, font=("Segoe UI", 8), anchor="e")
        self.status.pack(side="right", padx=(10, 2))

        self.pages = tk.Frame(self, bg=self.BG)
        self.pages.pack(fill="both", expand=True, padx=20, pady=12)
        self.home_page = tk.Frame(self.pages, bg=self.BG)
        self.watch_page = tk.Frame(self.pages, bg=self.PANEL, padx=14, pady=12)
        self.home_page.pack(fill="both", expand=True)

        toolbar = tk.Frame(self.home_page, bg=self.BG)
        toolbar.pack(fill="x", pady=(0, 9))
        tk.Label(toolbar, text="Browse channels", bg=self.BG, fg=self.TEXT,
                 font=("Segoe UI", 16, "bold")).pack(side="left")
        self.mode_button = self._button(toolbar, "♥ Favorites", self.toggle_favorites_view)
        self.mode_button.pack(side="right", padx=(8, 0))
        self.count_label = tk.Label(toolbar, text="0 channels", bg=self.BG, fg=self.MUTED,
                                    font=("Segoe UI", 9))
        self.count_label.pack(side="right")
        self.search = tk.StringVar()
        self.category = tk.StringVar(value="All categories")
        self.category_box = ttk.Combobox(toolbar, textvariable=self.category,
                                         values=("All categories",), state="readonly", width=20)
        self.category_box.pack(side="right", padx=(8, 0))
        self.category_box.bind("<<ComboboxSelected>>", lambda _e: self.render_channels())
        search = tk.Entry(self.home_page, textvariable=self.search, bg=self.PANEL, fg=self.TEXT,
                          insertbackground=self.TEXT, relief="flat", font=("Segoe UI", 10))
        search.pack(fill="x", ipady=8, pady=(0, 9))
        search.insert(0, "Filter channels…")
        search.bind("<FocusIn>", lambda _e: self._clear_placeholder(search))
        self.search.trace_add("write", lambda *_: self.render_channels())

        cards_shell = tk.Frame(self.home_page, bg=self.BG)
        cards_shell.pack(fill="both", expand=True)
        if self._pi_lite_tv:
            self.channel_list = ttk.Treeview(cards_shell, columns=("station", "category"),
                                             show="headings", selectmode="browse")
            self.channel_list.heading("station", text="CHANNEL")
            self.channel_list.heading("category", text="CATEGORY")
            self.channel_list.column("station", width=380, minwidth=150)
            self.channel_list.column("category", width=180, minwidth=90)
            list_scroll = ttk.Scrollbar(cards_shell, orient="vertical", command=self.channel_list.yview)
            self.channel_list.configure(yscrollcommand=list_scroll.set)
            self.channel_list.pack(side="left", fill="both", expand=True)
            list_scroll.pack(side="right", fill="y")
            self.channel_list.bind("<<TreeviewSelect>>", self._lite_channel_selected)
            self.channel_list.bind("<Double-1>", lambda _event: self.play_selected())
            self.channel_list.bind("<Return>", lambda _event: self.play_selected())
            self.more_cards_button = self._button(cards_shell, "Load more channels", self.load_more_cards)
            self.more_cards_button.pack(side="bottom", pady=(6, 0))
            self.more_cards_button.pack_forget()
            self._lite_channel_rows = {}
        else:
            self.cards_canvas = tk.Canvas(cards_shell, bg=self.BG, highlightthickness=0)
            cards_scroll = ttk.Scrollbar(cards_shell, orient="vertical", command=self.cards_canvas.yview)
            self.cards_canvas.configure(yscrollcommand=cards_scroll.set)
            self.cards_canvas.pack(side="left", fill="both", expand=True)
            cards_scroll.pack(side="right", fill="y")
            self.cards_inner = tk.Frame(self.cards_canvas, bg=self.BG)
            self.cards_window = self.cards_canvas.create_window((0, 0), window=self.cards_inner, anchor="nw")
            self.cards_inner.bind("<Configure>", lambda _e: self.cards_canvas.configure(
                scrollregion=self.cards_canvas.bbox("all")))
            self.cards_canvas.bind("<Configure>", lambda e: self.cards_canvas.itemconfigure(
                self.cards_window, width=e.width))
            self.cards_canvas.bind("<Enter>", lambda _e: self.bind_all("<MouseWheel>", self._cards_mousewheel))
            self.cards_canvas.bind("<Leave>", lambda _e: self.unbind_all("<MouseWheel>"))
            self.more_cards_button = self._button(self.cards_inner, "Load more cards", self.load_more_cards)

        self.now_playing = tk.Label(self.watch_page, text="Choose a channel to watch", bg=self.PANEL,
                                    fg=self.TEXT, font=("Segoe UI", 13, "bold"), anchor="w")
        self.now_playing.pack(fill="x", pady=(0, 9))
        self.video_surface = tk.Frame(self.watch_page, bg="#050709", highlightthickness=1,
                                      highlightbackground="#29333e")
        self.video_surface.pack(fill="both", expand=True)
        self.video_surface.bind("<Configure>", self._schedule_video_fit)
        self.video_hint = tk.Label(self.video_surface,
            text="Choose a channel card from Home to start watching",
            bg="#050709", fg="#83919f", font=("Segoe UI", 12))
        self.video_hint.place(relx=0.5, rely=0.5, anchor="center")

        controls = tk.Frame(self.watch_page, bg=self.PANEL)
        controls.pack(fill="x", pady=(10, 0))
        self._button(controls, "▶  Play", self.play_selected, primary=True).pack(side="left", padx=(0, 5))
        self._button(controls, "◀ Fav", lambda: self.play_favorite_step(-1)).pack(side="left", padx=3)
        self._button(controls, "Fav ▶", lambda: self.play_favorite_step(1)).pack(side="left", padx=3)
        self._button(controls, "Ⅱ  Pause", self.pause).pack(side="left", padx=5)
        self._button(controls, "■  Stop", self.stop).pack(side="left", padx=5)
        self.favorite_button = self._button(controls, "☆ Favorite", self.toggle_favorite)
        self.favorite_button.pack(side="left", padx=5)
        self.fullscreen_button = self._button(controls, "⛶ Fullscreen", self.toggle_fullscreen)
        self.fullscreen_button.pack(side="left", padx=5)
        self.aspect_button = self._button(controls, "Aspect: Auto", self.cycle_aspect)
        self.aspect_button.pack(side="left", padx=5)
        volume_control = tk.Frame(controls, bg=self.PANEL, width=285, height=34)
        volume_control.pack(side="right", padx=(8, 0))
        volume_control.pack_propagate(False)
        self.volume = tk.IntVar(value=75)
        tk.Label(volume_control, text="VOL", bg=self.PANEL, fg=self.MUTED,
                 font=("Segoe UI", 8, "bold")).pack(side="left", padx=(2, 7))
        self.volume_scale = tk.Scale(volume_control, from_=0, to=100, orient="horizontal",
            variable=self.volume, showvalue=False, resolution=1, length=195, width=5,
            sliderlength=15, bd=0, highlightthickness=0, relief="flat",
            bg=self.PANEL, fg=self.TEXT, troughcolor="#354653",
            activebackground="#79e1c2", command=self.set_volume)
        self.volume_scale.pack(side="left", fill="x", expand=True, padx=(0, 7))
        self.volume_bubble = tk.Label(volume_control, text="75%", width=4, bg="#293a49", fg=self.TEXT,
            font=("Segoe UI", 8, "bold"), padx=4, pady=3)
        self.volume_bubble.pack(side="right", padx=(0, 2))

        footer = tk.Label(self, text="Select a channel card to watch · public streams may be offline or region-restricted.",
                          bg=self.BG, fg=self.MUTED, font=("Segoe UI", 8), anchor="w")
        footer.pack(fill="x", padx=22, pady=(0, 7))

    def show_home(self):
        # Stop playback as soon as the viewer leaves the Watch screen.
        self.stop()
        self.watch_page.pack_forget()
        self.home_page.pack(fill="both", expand=True)

    def show_watch(self):
        self.home_page.pack_forget()
        self.watch_page.pack(fill="both", expand=True)

    def _cards_mousewheel(self, event):
        self.cards_canvas.yview_scroll(int(-event.delta / 120), "units")

    def _button(self, parent, text, command, primary=False):
        return tk.Button(parent, text=text, command=command,
                         bg="#278656" if primary else self.PANEL2,
                         activebackground="#39a96c" if primary else "#2b3948",
                         fg=self.TEXT, activeforeground=self.TEXT, relief="flat", bd=0,
                         cursor="hand2", padx=11, pady=8,
                         font=("Segoe UI", 9, "bold" if primary else "normal"))

    def _clear_placeholder(self, entry):
        if entry.get().startswith("Filter channels"):
            entry.delete(0, "end")

    def _init_player(self):
        self.vlc_instance = self.player = None
        if vlc is None:
            self.status.configure(text="Install VLC and python-vlc to watch streams")
            return
        try:
            self.vlc_instance = vlc.Instance("--quiet")
            self.player = self.vlc_instance.media_player_new()
            self.video_surface.update_idletasks()
            self._set_video_output(self.video_surface.winfo_id())
            self.player.audio_set_volume(self.volume.get())
        except Exception as exc:
            self.vlc_instance = self.player = None
            self.status.configure(text=f"VLC could not start: {exc}")

    def _select_playlist_preset(self, _event=None):
        url = PLAYLIST_PRESETS.get(self.playlist_preset.get())
        if url:
            self.playlist_url.set(url)

    def load_selected_preset(self):
        self._select_playlist_preset()
        self.load_playlist_url()

    def _load_text_async(self, fetch, source_name):
        if self.loading:
            return
        self.loading = True
        self.status.configure(text=f"Loading {source_name}…")
        def run():
            try:
                text = fetch()
                channels = parse_m3u(text)
                self.events.put((self._playlist_loaded, (channels, source_name), None))
            except Exception as exc:
                self.events.put((self._playlist_loaded, None, str(exc)))
        threading.Thread(target=run, daemon=True).start()

    def load_public_guide(self):
        def fetch():
            request = urllib.request.Request(FREE_TV_GUIDE,
                headers={"User-Agent": "WorldLiveTV/1.0"})
            with urllib.request.urlopen(request, timeout=45) as response:
                return response.read().decode("utf-8-sig", errors="replace")
        self.playlist_url.set(FREE_TV_GUIDE)
        self._load_text_async(fetch, "public TV guide")

    def load_playlist_url(self):
        url = self.playlist_url.get().strip()
        if not url.lower().startswith(("https://", "http://")):
            messagebox.showerror("Playlist URL", "Enter a playlist URL beginning with http:// or https://")
            return
        def fetch():
            request = urllib.request.Request(url, headers={"User-Agent": "WorldLiveTV/1.0"})
            with urllib.request.urlopen(request, timeout=45) as response:
                return response.read().decode("utf-8-sig", errors="replace")
        self._load_text_async(fetch, "playlist")

    def open_playlist_file(self):
        path = filedialog.askopenfilename(title="Open a TV playlist",
            filetypes=[("M3U playlists", "*.m3u *.m3u8"), ("All files", "*.*")])
        if not path:
            return
        def fetch():
            return Path(path).read_text(encoding="utf-8-sig", errors="replace")
        self._load_text_async(fetch, Path(path).name)

    def _playlist_loaded(self, result, error):
        self.loading = False
        if error:
            self.status.configure(text="Could not load playlist. Check the URL or internet connection.")
            messagebox.showerror("Could not load playlist", str(error))
            return
        # A delayed guide response must not reset a Favorites/Home/Watch view
        # or stop a stream the user started while the guide was downloading.
        was_favorites = self.showing_favorites
        self.channels, source_name = result
        self.showing_favorites = was_favorites
        self._refresh_categories()
        self.mode_button.configure(text="All channels" if self.showing_favorites else "♥ Favorites")
        self.render_channels()
        self.status.configure(text=f"Loaded {len(self.channels):,} channels · {source_name}")

    def render_channels(self):
        if self._pi_lite_tv:
            if not hasattr(self, "channel_list"):
                return
        elif not hasattr(self, "cards_inner"):
            return
        query = self.search.get().strip().casefold()
        if query.startswith("filter channels"):
            query = ""
        source = list(self.favorites.values()) if self.showing_favorites else self.channels
        selected_category = self.category.get()
        rows = [channel for channel in source
                if not query or query in channel.get("name", "").casefold()
                or query in channel.get("group", "").casefold()]
        if selected_category and selected_category != "All categories":
            rows = [channel for channel in rows
                    if channel.get("group", "TV").strip() == selected_category]
        self.visible_channels = rows
        if self._pi_lite_tv:
            self._lite_channel_rows.clear()
            for item in self.channel_list.get_children():
                self.channel_list.delete(item)
            shown = rows[:self.card_limit]
            for index, channel in enumerate(shown):
                iid = str(index)
                name = channel.get("name", "TV channel")
                if self._channel_key(channel) in self.favorites:
                    name = "★  " + name
                self.channel_list.insert("", "end", iid=iid,
                                         values=(name, channel.get("group", "TV")))
                self._lite_channel_rows[iid] = channel
            if len(rows) > self.card_limit:
                self.more_cards_button.configure(
                    text=f"Load more channels  ·  {len(rows) - self.card_limit:,} remaining")
                self.more_cards_button.pack(side="bottom", pady=(6, 0))
            else:
                self.more_cards_button.pack_forget()
            self.count_label.configure(text=f"{len(shown):,} of {len(rows):,} channels")
            self._sync_favorite_button()
            return
        self.logo_labels = {}
        for widget in self.cards_inner.winfo_children():
            if widget is not self.more_cards_button:
                widget.destroy()
        shown = rows[:self.card_limit]
        columns = 6
        for column in range(columns):
            self.cards_inner.grid_columnconfigure(column, weight=1, uniform="tvcard")
        for index, channel in enumerate(shown):
            row, column = divmod(index, columns)
            card = tk.Frame(self.cards_inner, bg="#19232d", padx=8, pady=8,
                            highlightthickness=1, highlightbackground="#2c3a48", cursor="hand2")
            card.grid(row=row, column=column, sticky="nsew", padx=6, pady=6)
            card.configure(width=166, height=147)
            card.grid_propagate(False)
            poster = tk.Frame(card, bg="#233544", height=76, cursor="hand2")
            poster.pack(fill="x", expand=False, pady=(0, 7))
            poster.pack_propagate(False)
            image_label = tk.Label(poster, text=self._channel_initials(channel), bg="#233544",
                                   fg="#91d9ce", font=("Segoe UI", 24, "bold"), cursor="hand2")
            image_label.pack(expand=True)
            favorite_badge = None
            if self._channel_key(channel) in self.favorites:
                favorite_badge = tk.Label(poster, text="★", bg="#233544", fg="#ffd43b",
                                          font=("Segoe UI", 15, "bold"), cursor="hand2")
                favorite_badge.place(relx=1.0, x=-5, y=3, anchor="ne")
            name_label = tk.Label(card, text=channel.get("name", "TV channel"), bg="#19232d",
                                  fg=self.TEXT, font=("Segoe UI", 9, "bold"),
                                  wraplength=145, justify="left", anchor="w", cursor="hand2")
            name_label.pack(fill="x", anchor="w")
            group_label = tk.Label(card, text=channel.get("group", "TV"), bg="#19232d",
                                   fg=self.MUTED, font=("Segoe UI", 8), anchor="w", cursor="hand2")
            group_label.pack(fill="x", anchor="w", pady=(3, 0))
            command = lambda item=channel: self._watch_channel(item)
            card_widgets = [card, poster, image_label, name_label, group_label]
            if favorite_badge is not None:
                card_widgets.append(favorite_badge)
            for widget in card_widgets:
                widget.bind("<Button-1>", lambda _event, callback=command: callback())
                widget.bind("<Enter>", lambda _event, target=card: target.configure(
                    highlightbackground="#66cbbb", bg="#213442"))
                widget.bind("<Leave>", lambda _event, target=card: target.configure(
                    highlightbackground="#2c3a48", bg="#19232d"))
            logo = channel.get("logo", "")
            if logo.lower().startswith(("https://", "http://")):
                self._request_channel_logo(logo, image_label)
        self.more_cards_button.grid_forget()
        if len(rows) > self.card_limit:
            self.more_cards_button.configure(text=f"Load more cards  ·  {len(rows) - self.card_limit:,} left")
            self.more_cards_button.grid(row=(len(shown) + columns - 1) // columns,
                                        column=0, columnspan=columns, pady=18)
        self.count_label.configure(text=f"{len(shown):,} of {len(rows):,} cards")
        self._sync_favorite_button()

    def _lite_channel_selected(self, _event=None):
        if not self._pi_lite_tv:
            return
        selected = self.channel_list.selection()
        self.selected_channel_data = self._lite_channel_rows.get(selected[0]) if selected else None
        self._sync_favorite_button()

    def selected_channel(self):
        return self.selected_channel_data

    @staticmethod
    def _channel_initials(channel):
        words = (channel.get("name") or "TV").strip().split()
        return "".join(word[0] for word in words[:2]).upper() or "TV"

    def load_more_cards(self):
        self.card_limit += self.card_batch_size
        self.render_channels()

    def _watch_channel(self, channel):
        self.selected_channel_data = channel
        self.play_selected()
        self.show_watch()

    def _request_channel_logo(self, url, label):
        self.logo_labels.setdefault(url, []).append(label)
        image = self.logo_images.get(url)
        if image:
            label.configure(image=image, text="")
            label.image = image
            return
        if url in self.logo_pending:
            return
        self.logo_pending.add(url)
        def fetch():
            try:
                request = urllib.request.Request(url, headers={"User-Agent": "SurakHomeTV/1.0"})
                with urllib.request.urlopen(request, timeout=12) as response:
                    image_limit = 400_000 if os.environ.get("SURAK_PI_LITE") == "1" else 1_500_000
                    data = response.read(image_limit)
                self.logo_events.put((url, data, None))
            except Exception as exc:
                self.logo_events.put((url, None, str(exc)))
        self.logo_executor.submit(fetch)

    def _apply_logo_events(self):
        try:
            while True:
                url, data, error = self.logo_events.get_nowait()
                self.logo_pending.discard(url)
                if error or not data:
                    continue
                try:
                    if Image is not None:
                        source = Image.open(BytesIO(data)).convert("RGBA")
                        source.thumbnail((150, 76))
                        photo = ImageTk.PhotoImage(source, master=self)
                    else:
                        photo = tk.PhotoImage(data=base64.b64encode(data).decode("ascii"), master=self)
                        factor = max(1, (photo.width() + 149) // 150, (photo.height() + 75) // 76)
                        if factor > 1:
                            photo = photo.subsample(factor, factor)
                    self.logo_images[url] = photo
                    for label in self.logo_labels.get(url, []):
                        if label.winfo_exists():
                            label.configure(image=photo, text="")
                            label.image = photo
                except Exception:
                    # Keep the card's initials when the logo format is unsupported.
                    continue
        except queue.Empty:
            pass

    @staticmethod
    def _channel_key(channel):
        return (channel or {}).get("url", "")

    def _sync_favorite_button(self):
        if not hasattr(self, "favorite_button"):
            return
        channel = self.selected_channel() or self.current
        saved = bool(channel and self._channel_key(channel) in self.favorites)
        self.favorite_button.configure(text="★ Saved" if saved else "☆ Favorite")

    def toggle_favorites_view(self):
        self.showing_favorites = not self.showing_favorites
        self.card_limit = self.card_batch_size
        self.category.set("All categories")
        self.search.set("")
        self._refresh_categories()
        self.mode_button.configure(text="All channels" if self.showing_favorites else "♥ Favorites")
        self.render_channels()
        self.status.configure(text=("Showing saved favorites" if self.showing_favorites
                                    else f"Showing playlist · {len(self.channels):,} channels"))

    def _refresh_categories(self):
        """Populate the category filter from the currently visible channel source."""
        source = self.favorites.values() if self.showing_favorites else self.channels
        categories = sorted({str(channel.get("group", "TV")).strip() or "TV"
                             for channel in source}, key=str.casefold)
        values = ["All categories", *categories]
        self.category_box.configure(values=values)
        if self.category.get() not in values:
            self.category.set("All categories")

    def toggle_favorite(self):
        channel = self.selected_channel() or self.current
        if not channel:
            self.status.configure(text="Choose a channel before saving it")
            return
        key = self._channel_key(channel)
        if not key:
            self.status.configure(text="This channel has no stream URL to save")
            return
        if key in self.favorites:
            del self.favorites[key]
            self.status.configure(text=f"Removed {channel.get('name', 'channel')} from favorites")
        else:
            self.favorites[key] = channel
            self.status.configure(text=f"Saved {channel.get('name', 'channel')} to favorites")
        self._save_favorites()
        self.render_channels()

    def play_favorite_step(self, direction):
        favorites = list(self.favorites.values())
        if not favorites:
            self.status.configure(text="Save channels as favorites to use next/previous")
            return
        current_key = self._channel_key(self.current)
        favorite_keys = [self._channel_key(channel) for channel in favorites]
        if current_key not in favorite_keys:
            index = 0 if direction > 0 else len(favorites) - 1
        else:
            index = (favorite_keys.index(current_key) + direction) % len(favorites)
        channel = favorites[index]
        if self.player is None:
            self.status.configure(text="VLC playback unavailable")
            return
        try:
            self._start_channel(channel)
            self.selected_channel_data = channel
            self.show_watch()
            self.status.configure(text=f"Favorite {index + 1} of {len(favorites)} · {channel.get('name', 'TV')}")
        except Exception as exc:
            self.status.configure(text=f"Could not play favorite: {exc}")

    def toggle_fullscreen(self):
        if self.fullscreen:
            self._leave_fullscreen()
            return
        if not self.player or not self.current:
            self.status.configure(text="Start a channel before entering fullscreen")
            return
        window = tk.Toplevel(self)
        self.fullscreen_window = window
        window.configure(bg="#050709")
        window.attributes("-fullscreen", True)
        window.protocol("WM_DELETE_WINDOW", self._leave_fullscreen)

        bar = tk.Frame(window, bg="#111a23", padx=14, pady=7)
        bar.pack(fill="x", side="top")
        self.fullscreen_title_label = tk.Label(
            bar, text=f"SURAK HOME TV   ·   {self.current.get('name', 'LIVE TV')}",
            bg="#111a23", fg=self.TEXT, font=("Segoe UI", 10, "bold"))
        self.fullscreen_title_label.pack(side="left")
        tk.Button(bar, text="Exit fullscreen  ✕", command=self._leave_fullscreen,
                  bg="#263543", fg=self.TEXT, activebackground="#344756",
                  activeforeground=self.TEXT, relief="flat", bd=0,
                  padx=12, pady=5, cursor="hand2").pack(side="right")
        surface = tk.Frame(window, bg="#050709")
        surface.pack(fill="both", expand=True)
        surface.bind("<Configure>", self._schedule_video_fit)
        window.update_idletasks()
        self.fullscreen_video = surface
        self.fullscreen = True
        self._install_appcommand_hook(window)
        self._install_appcommand_hook(surface)
        try:
            channel = self.current
            self.player.stop()
            self._set_video_output(surface.winfo_id())
            window.focus_force()
            self._start_channel(channel)
        except Exception as exc:
            try:
                self.player.stop()
                self._set_video_output(self.video_surface.winfo_id())
            except Exception:
                pass
            self._remove_appcommand_hook(surface)
            self._remove_appcommand_hook(window)
            self.fullscreen = False
            window.destroy()
            self.fullscreen_window = self.fullscreen_video = None
            self.status.configure(text=f"Could not enter fullscreen: {exc}")
            return
        self.fullscreen_button.configure(text="⛶ Exit fullscreen")

    def _leave_fullscreen(self, restart=True):
        if not self.fullscreen:
            return
        channel = self.current
        try:
            if self.player:
                self.player.stop()
            if self.player and self.video_surface.winfo_exists():
                self._set_video_output(self.video_surface.winfo_id())
        except Exception:
            pass
        window = self.fullscreen_window
        fullscreen_surface = self.fullscreen_video
        self.fullscreen = False
        self.fullscreen_window = self.fullscreen_video = None
        self.fullscreen_title_label = None
        if window and window.winfo_exists():
            if fullscreen_surface and fullscreen_surface.winfo_exists():
                self._remove_appcommand_hook(fullscreen_surface)
            self._remove_appcommand_hook(window)
            window.destroy()
        if hasattr(self, "fullscreen_button"):
            self.fullscreen_button.configure(text="⛶ Fullscreen")
        if restart and channel and self.player:
            self._start_channel(channel)
        try:
            self.lift()
        except tk.TclError:
            pass

    def _fullscreen_key(self, _event=None):
        self.toggle_fullscreen()
        return "break"

    def _escape_fullscreen(self, _event=None):
        if self.fullscreen:
            self._leave_fullscreen()
            return "break"

    def _poll_fullscreen_hotkeys(self):
        """Watch F11/Escape while our Tk or embedded VLC window has focus."""
        if self._view_suspended:
            return
        if sys.platform != "win32":
            return
        try:
            user32 = ctypes.windll.user32
            user32.GetForegroundWindow.restype = ctypes.c_void_p
            user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
            user32.GetAsyncKeyState.restype = ctypes.c_short
            user32.IsChild.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
            user32.IsChild.restype = ctypes.c_bool
            active_hwnd = user32.GetForegroundWindow() or 0
            roots = [self.winfo_id()]
            if self.fullscreen_window and self.fullscreen_window.winfo_exists():
                roots.append(self.fullscreen_window.winfo_id())
            app_active = self.winfo_ismapped() and any(
                active_hwnd == hwnd or user32.IsChild(hwnd, active_hwnd) for hwnd in roots
            )
            f11_down = bool(user32.GetAsyncKeyState(0x7A) & 0x8000)
            escape_down = bool(user32.GetAsyncKeyState(0x1B) & 0x8000)
            media_next_down = bool(user32.GetAsyncKeyState(0xB0) & 0x8000)
            media_previous_down = bool(user32.GetAsyncKeyState(0xB1) & 0x8000)
            media_stop_down = bool(user32.GetAsyncKeyState(0xB2) & 0x8000)
            media_play_pause_down = bool(user32.GetAsyncKeyState(0xB3) & 0x8000)
            if app_active and f11_down and not self._f11_down:
                self.toggle_fullscreen()
            if app_active and escape_down and not self._escape_down and self.fullscreen:
                self._leave_fullscreen()
            if app_active and media_next_down and not self._media_next_down:
                self._handle_appcommand(11)
            if app_active and media_previous_down and not self._media_previous_down:
                self._handle_appcommand(12)
            if app_active and media_play_pause_down and not self._media_play_pause_down:
                self._handle_appcommand(14)
            if app_active and media_stop_down and not self._media_stop_down:
                self._handle_appcommand(13)
            self._f11_down = f11_down
            self._escape_down = escape_down
            self._media_next_down = media_next_down
            self._media_previous_down = media_previous_down
            self._media_play_pause_down = media_play_pause_down
            self._media_stop_down = media_stop_down
        except Exception:
            pass
        try:
            while True:
                command = self.appcommand_events.get_nowait()
                if self.winfo_ismapped():
                    self._handle_appcommand(command)
        except queue.Empty:
            pass
        if self.winfo_exists():
            self.after(60, self._poll_fullscreen_hotkeys)

    def _install_appcommand_hook(self, window):
        """Capture Windows media transport commands sent to the app window."""
        if sys.platform != "win32":
            return
        try:
            hwnd = int(window.winfo_id())
            if hwnd in self._wndproc_hooks:
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
                        app.appcommand_events.put(command)
                        return 1
                return call_proc(old_proc, h_wnd, message, w_param, l_param)

            old_proc = set_proc(hwnd, -4, ctypes.cast(window_proc, ctypes.c_void_p))
            if old_proc:
                self._wndproc_hooks[hwnd] = (window_proc, old_proc)
        except Exception:
            # The virtual media-key polling remains as a fallback.
            return

    def _remove_appcommand_hook(self, window):
        if sys.platform != "win32":
            return
        try:
            hwnd = int(window.winfo_id())
            entry = self._wndproc_hooks.pop(hwnd, None)
            if not entry:
                return
            _callback, old_proc = entry
            user32 = ctypes.windll.user32
            set_proc = getattr(user32, "SetWindowLongPtrW", None) or user32.SetWindowLongW
            set_proc.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
            set_proc.restype = ctypes.c_void_p
            set_proc(hwnd, -4, old_proc)
        except Exception:
            return

    def _handle_appcommand(self, command):
        # Avoid double actions when both a media virtual key and WM_APPCOMMAND arrive.
        now = time.monotonic()
        previous, previous_time = self._last_media_command
        if previous == command and now - previous_time < 0.22:
            return
        self._last_media_command = (command, now)
        if command == 11:       # Next track
            self.play_favorite_step(1)
        elif command == 12:     # Previous track
            self.play_favorite_step(-1)
        elif command == 14:     # Play/pause
            self.toggle_play_pause()
        elif command == 46:     # Play
            self.resume()
        elif command == 47:     # Pause
            self.pause()
        elif command == 13:     # Stop
            self.stop()

    def play_selected(self):
        channel = self.selected_channel() or self.current
        if not channel:
            self.status.configure(text="Choose a channel from the list first")
            return
        if self.player is None:
            messagebox.showerror("VLC playback unavailable",
                "Install VLC Media Player for Windows and run:\npy -m pip install -r requirements.txt")
            return
        try:
            self._start_channel(channel)
            self.show_watch()
        except Exception as exc:
            self.status.configure(text=f"Could not start stream: {exc}")

    def _start_channel(self, channel):
        # VLC may wait while an old network stream shuts down. Keep that work
        # off Tk's UI thread so repeated channel surfing cannot freeze the app.
        self.playback_generation += 1
        generation = self.playback_generation
        self.video_hint.place_forget()
        self.current = channel
        self.now_playing.configure(text=channel.get("name", "Live TV"))
        if self.fullscreen_title_label:
            self.fullscreen_title_label.configure(
                text=f"SURAK HOME TV   ·   {channel.get('name', 'LIVE TV')}"
            )
        self._sync_favorite_button()
        self.status.configure(text=f"Connecting · {channel.get('group') or 'Live stream'}")
        hwnd = (self.fullscreen_video.winfo_id()
                if self.fullscreen and self.fullscreen_video
                else self.video_surface.winfo_id())
        options = list(channel.get("options", []))
        volume = self.volume.get()
        _label, aspect = self.aspect_modes[self.aspect_index]
        self.playback_executor.submit(
            self._open_stream_worker, generation, channel, hwnd, options, volume, aspect
        )

    def _open_stream_worker(self, generation, channel, hwnd, options, volume, aspect):
        error = None
        media = None
        try:
            if generation != self.playback_generation:
                return
            self.player.stop()
            self.player.set_media(None)
            previous_media = self.active_media
            self.active_media = None
            if previous_media is not None:
                previous_media.release()
            if generation != self.playback_generation:
                return
            media = self.vlc_instance.media_new(channel["url"])
            for option in options:
                media.add_option(option if option.startswith(":") else ":" + option)
            # More buffer helps HD streams ride through brief network dips.
            media.add_option(":network-caching=5000")
            if generation != self.playback_generation:
                media.release()
                return
            self.player.set_media(media)
            self.active_media = media
            self._set_video_output(hwnd)
            self.player.video_set_scale(0)
            self.player.video_set_aspect_ratio(aspect)
            self.player.audio_set_mute(False)
            self.player.audio_set_volume(volume)
            self.player.play()
            # Reapply after play: some VLC builds retain the previous stop
            # mute flag until the stream's audio output has been created.
            self.player.audio_set_mute(False)
            self.player.audio_set_volume(volume)
        except Exception as exc:
            error = str(exc)
            if media is not None and self.active_media is not media:
                try:
                    media.release()
                except Exception:
                    pass
        self.events.put((self._playback_started, (generation, channel), error))

    def _set_video_output(self, window_id):
        """Attach libVLC video to a Tk surface on the current desktop OS."""
        if sys.platform == "win32":
            self.player.set_hwnd(window_id)
        elif sys.platform == "darwin":
            self.player.set_nsobject(window_id)
        else:
            # Raspberry Pi OS uses X11/XWayland for Tk's video surface.
            self.player.set_xwindow(window_id)

    def _playback_started(self, result, error):
        generation, channel = result
        if generation != self.playback_generation or not self.winfo_exists():
            return
        if error:
            self.status.configure(text=f"Could not start stream: {error}")
            return
        self.after(450, lambda g=generation: self._restore_stream_audio(g))
        self.after(1300, lambda g=generation: self._restore_stream_audio(g))
        self.after(2600, self._check_stream)

    def _restore_stream_audio(self, generation):
        if generation != self.playback_generation or not self.player:
            return
        level = max(0, min(100, int(self.volume.get())))
        try:
            self.player.audio_set_volume(level)
            self.player.audio_set_mute(level == 0)
        except Exception:
            pass

    def cycle_aspect(self):
        self.aspect_index = (self.aspect_index + 1) % len(self.aspect_modes)
        label, _aspect = self.aspect_modes[self.aspect_index]
        self.aspect_button.configure(text=f"Aspect: {label}")
        self._apply_video_aspect()

    def _apply_video_aspect(self):
        if not self.player:
            return
        try:
            _label, aspect = self.aspect_modes[self.aspect_index]
            self.player.video_set_scale(0)  # Fit video to the output window.
            self.player.video_set_aspect_ratio(aspect)  # None keeps source aspect ratio.
        except Exception:
            pass

    def _schedule_video_fit(self, _event=None):
        if self._video_fit_job:
            try:
                self.after_cancel(self._video_fit_job)
            except tk.TclError:
                pass
        self._video_fit_job = self.after(120, self._fit_video)

    def _fit_video(self):
        self._video_fit_job = None
        self._apply_video_aspect()

    def _check_stream(self):
        if self.player and self.current:
            if self.player.get_state() == vlc.State.Error:
                self.status.configure(text="Stream failed · try another channel")
            elif self.player.is_playing():
                self.status.configure(text=f"LIVE · {self.current.get('group') or 'TV'}")

    def pause(self):
        if self.player:
            self.player.set_pause(1)
            self.status.configure(text="Paused")

    def resume(self):
        if self.player and self.current:
            try:
                self.player.audio_set_mute(False)
                self.player.audio_set_volume(self.volume.get())
            except Exception:
                pass
            self.player.set_pause(0)
            self.status.configure(text=f"LIVE · {self.current.get('group') or 'TV'}")
        else:
            self.play_selected()

    def toggle_play_pause(self):
        if self.player and self.current and self.player.is_playing():
            self.pause()
        else:
            self.resume()

    def stop(self):
        self.playback_generation += 1
        if self.fullscreen:
            self._leave_fullscreen(restart=False)
        if self.player:
            self.playback_executor.submit(self._stop_stream_worker)
        self.current = None
        if hasattr(self, "video_hint"):
            self.video_hint.place(relx=0.5, rely=0.5, anchor="center")
        if hasattr(self, "now_playing"):
            self.now_playing.configure(text="Choose a channel to watch")
        if hasattr(self, "status"):
            self.status.configure(text="Stopped" if vlc else "VLC playback unavailable")
        self._sync_favorite_button()

    def _stop_stream_worker(self):
        try:
            self.player.stop()
            self.player.set_media(None)
        except Exception:
            pass
        previous_media = self.active_media
        self.active_media = None
        if previous_media is not None:
            try:
                previous_media.release()
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
                    self.status.configure(text=f"Could not change audio volume: {exc}")
        if self._volume_applied != self._volume_target:
            self._volume_job = self.after(18, self._ramp_volume)

    def _drain_events(self):
        if self._view_suspended:
            return
        try:
            while True:
                callback, result, error = self.events.get_nowait()
                callback(result, error)
        except queue.Empty:
            pass
        self._apply_logo_events()
        self.after(140, self._drain_events)

    def suspend_view(self):
        if not self._view_suspended:
            self.stop()
            self._view_suspended = True

    def resume_view(self):
        if self._view_suspended:
            self._view_suspended = False
            self.after(140, self._drain_events)
            self.after(100, self._poll_fullscreen_hotkeys)

    def close(self):
        if self.fullscreen:
            self._leave_fullscreen(restart=False)
        if self.player:
            self.playback_generation += 1
            try:
                self.player.audio_set_mute(True)
            except Exception:
                pass
            self.playback_executor.submit(self._stop_stream_worker)
        self._remove_appcommand_hook(self.video_surface)
        self._remove_appcommand_hook(self)
        self.logo_executor.shutdown(wait=False, cancel_futures=True)
        self.playback_executor.shutdown(wait=False, cancel_futures=False)
        self.destroy()
        if self._owns_root:
            self.root.destroy()


if __name__ == "__main__":
    app = LiveTV()
    app.root.mainloop()
