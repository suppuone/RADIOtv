"""Separate Windows radio player with a clickable, offline world map."""
from __future__ import annotations

import json
import math
import queue
import tkinter as tk
from tkinter import ttk
from pathlib import Path
from datetime import datetime, timedelta, timezone
import urllib.parse
import urllib.request
import threading
import xml.etree.ElementTree as ET
import html
import re
import os
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from radio_app import WorldRadio, api_get, station_id, PAGE_SIZE

APP_DIR = Path(__file__).resolve().parent
MAP_FILE = APP_DIR / "countries.geojson"
LITE_MAP_FILE = APP_DIR / "countries_lite.json"
FAVORITES_FILE = APP_DIR / "map_favorites.json"
IPRD_CATALOG_URL = "https://iprd-org.github.io/iprd/site_data/metadata/catalog.json"
VERIFIED_RAW_BASE = "https://raw.githubusercontent.com/eyalev/verified-radio-streams/main"
VERIFIED_INDEX_URL = VERIFIED_RAW_BASE + "/stations/index.json"
VERIFIED_ALL_M3U_URL = VERIFIED_RAW_BASE + "/m3u/all.m3u"
RADIO_SOURCES = ("Radio Browser", "IPRD", "Verified Radio")
NEWS_FEEDS = {
    "WORLD": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "INDIA": "https://feeds.bbci.co.uk/news/world/asia/india/rss.xml",
}
REGIONAL_STATES = (
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa",
    "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala",
    "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland",
    "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal", "Andaman and Nicobar Islands",
    "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu", "Delhi", "Jammu and Kashmir",
    "Ladakh", "Lakshadweep", "Puducherry",
)
NEWS_SECTIONS = (*NEWS_FEEDS, "REGIONAL INDIA")


class WorldRadioMap(WorldRadio):
    BG = "#0b1118"
    PANEL = "#141e28"
    PANEL2 = "#202d37"
    TEXT = "#eef5f4"
    MUTED = "#91a6ad"
    GREEN = "#55d6b0"

    def __init__(self, master=None):
        self._pi_lite = os.environ.get("SURAK_PI_LITE") == "1"
        self._ticker_interval = 110 if self._pi_lite else 45
        self._wave_interval = 260 if self._pi_lite else 140
        self._meter_interval = 220 if self._pi_lite else 100
        self._data_poll_interval = 500 if self._pi_lite else 160
        self._radio_suspended = False
        self._radio_after_ids = set()
        self._default_country_pending = True
        self.meter_phase = 0.0
        self.iprd_catalog = None
        self.verified_country_cache = {}
        self.verified_all_cache = None
        self.country_shapes = []
        self.country_by_name = {}
        self.country_by_code = {}
        self.map_country_code = None
        self.map_country_name = None
        self.wave_center = None
        self.wave_phase = 0
        self.weather_events = queue.Queue()
        self.news_events = queue.Queue()
        self.news_headlines = {}
        self.news_section = "WORLD"
        self.news_request_ids = {}
        self.news_ticker_message = "Loading headlines…"
        self.news_ticker_item = None
        self.news_ticker_x = 0
        self.country_timezone = None
        self.country_time_name = None
        self.country_utc_offset_seconds = None
        self.country_timezone_status = "local"
        self.weather_color = "#47c98b"
        self.weather_ticker_message = "Select a country to see local weather and the next hours"
        self.weather_ticker_item = None
        self.weather_ticker_x = 0
        super().__init__(master)
        if self._owns_root:
            self.root.title("World Radio — Map Edition")
            self.root.geometry("1240x790")
            self.root.minsize(960, 650)
        self.after(500, self._tick_clock)
        if not self._pi_lite:
            self.after(self._wave_interval, self._animate_waves)
        self.after(self._data_poll_interval, self._drain_weather_events)
        self.after(self._data_poll_interval, self._drain_news_events)
        self.after(450, self._load_news_feeds)
        if not self._pi_lite:
            self.after(self._ticker_interval, self._tick_weather_ticker)
            self.after(self._ticker_interval, self._tick_news_ticker)
            self.after(self._meter_interval, self._animate_audio_meter)

    def after(self, ms, func=None, *args):
        """Track this view's Tk callbacks so mode switches can pause them all."""
        if getattr(self, "_radio_suspended", False):
            return None
        if func is None:
            return super().after(ms)
        job_id = None

        def run():
            self._radio_after_ids.discard(job_id)
            if not self._radio_suspended and self.winfo_exists():
                func(*args)

        job_id = super().after(ms, run)
        self._radio_after_ids.add(job_id)
        return job_id

    def after_cancel(self, job_id):
        self._radio_after_ids.discard(job_id)
        return super().after_cancel(job_id)

    def suspend_view(self):
        """Stop radio playback and pause all radio-only background UI work."""
        if self._radio_suspended:
            self.stop()
            return
        self._radio_suspended = True
        for job_id in tuple(self._radio_after_ids):
            try:
                super().after_cancel(job_id)
            except tk.TclError:
                pass
        self._radio_after_ids.clear()
        self._volume_job = None
        self.stop()

    def resume_view(self):
        """Restart the radio view's event pumps and visual updates."""
        if not self._radio_suspended:
            return
        self._radio_suspended = False
        self.after(120, self._drain_events)
        self.after(100, self._poll_remote_controls)
        self.after(500, self._tick_clock)
        if not self._pi_lite:
            self.after(self._wave_interval, self._animate_waves)
        self.after(self._data_poll_interval, self._drain_weather_events)
        self.after(self._data_poll_interval, self._drain_news_events)
        if not self._pi_lite:
            self.after(self._ticker_interval, self._tick_weather_ticker)
            self.after(self._ticker_interval, self._tick_news_ticker)
            self.after(self._meter_interval, self._animate_audio_meter)
        if not self.news_headlines:
            self.after(100, self._load_news_feeds)
        if self.map_country_name and self.country_timezone_status != "ready":
            self._load_weather(self.map_country_name, self.map_country_code)
        if self._volume_applied != self._volume_target and self._volume_job is None:
            self._volume_job = self.after(18, self._ramp_volume)

    def load_favorites(self):
        try:
            return json.loads(FAVORITES_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

    def save_favorites(self):
        FAVORITES_FILE.write_text(json.dumps(self.favorites, ensure_ascii=False, indent=2), encoding="utf-8")

    def _build_ui(self):
        header = tk.Frame(self, bg=self.BG)
        header.pack(fill="x", padx=22, pady=(16, 10))
        tk.Label(header, text="WORLD RADIO" if self._pi_lite else "◉  WORLD RADIO", bg=self.BG, fg=self.TEXT,
                 font=("DejaVu Sans", 16 if self._pi_lite else 21, "bold")).pack(side="left")
        tk.Label(header, text="CHOOSE A COUNTRY OR BROWSE WORLDWIDE" if self._pi_lite else "MAP EDITION  ·  CLICK A COUNTRY TO BROWSE", bg=self.BG,
                 fg=self.MUTED, font=("Segoe UI", 9, "bold")).pack(side="right", pady=9)
        self.clock_label = tk.Label(header, text="LOCAL  --:--", bg=self.BG, fg="#e6c77a",
                                    font=("Consolas", 12, "bold"))
        self.clock_label.pack(side="right", padx=18, pady=8)

        controls = tk.Frame(self, bg=self.PANEL, padx=12, pady=10)
        controls.pack(fill="x", padx=20)
        source_box = tk.Frame(controls, bg=self.PANEL)
        source_box.pack(side="right", padx=(8, 0))
        tk.Label(source_box, text="SOURCE", bg=self.PANEL, fg=self.MUTED,
                 font=("Segoe UI", 8, "bold")).pack(side="left", padx=(0, 6))
        self.source_var = tk.StringVar(value=RADIO_SOURCES[0])
        self.source_picker = ttk.Combobox(source_box, textvariable=self.source_var,
            values=RADIO_SOURCES, state="readonly", width=17)
        self.source_picker.pack(side="left")
        self.source_picker.bind("<<ComboboxSelected>>", self._source_changed)
        self.search = tk.StringVar()
        entry = tk.Entry(controls, textvariable=self.search, bg=self.PANEL2, fg=self.TEXT,
                         insertbackground=self.TEXT, relief="flat", font=("Segoe UI", 10))
        entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 7))
        entry.insert(0, "Search all stations…")
        entry.bind("<FocusIn>", lambda _e: self._clear_placeholder(entry))
        entry.bind("<Return>", lambda _e: self.search_directory())
        self._button(controls, "Search", self.search_directory, primary=True).pack(side="left", padx=3)
        self._button(controls, "Popular worldwide", self.load_directory).pack(side="left", padx=3)
        self._button(controls, "♥ Favorites", self.show_favorites).pack(side="left", padx=3)

        content = tk.Frame(self, bg=self.BG)
        content.pack(fill="both", expand=True, padx=20, pady=(12, 10))
        left = tk.Frame(content, bg=self.PANEL, padx=12, pady=10)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        top = tk.Frame(left, bg=self.PANEL)
        top.pack(fill="x", pady=(0, 7))
        self.map_caption = tk.Label(top, text="COUNTRY  ·  Select a country" if self._pi_lite else "WORLD MAP  ·  Select a country", bg=self.PANEL,
                                    fg=self.TEXT, font=("Segoe UI", 10, "bold"))
        self.map_caption.pack(side="left")
        self.country_choice = tk.StringVar(value="Choose a country…")
        self.country_picker = ttk.Combobox(top, textvariable=self.country_choice, state="readonly", width=25)
        self.country_picker.pack(side="right", padx=(8, 0))
        self.country_picker.bind("<<ComboboxSelected>>", self._country_picker_selected)
        self._button(top, "Clear", self.clear_map_selection).pack(side="right")
        if self._pi_lite:
            self.country_clock_label = tk.Label(
                left, text="Choose a country to list its stations", bg=self.PANEL,
                fg=self.MUTED, font=("DejaVu Sans", 11), anchor="center")
            self.country_clock_label.pack(fill="both", expand=True, padx=20, pady=20)
        else:
            self.map_canvas = tk.Canvas(left, bg="#0e1822", highlightthickness=0, cursor="hand2")
            self.map_canvas.pack(fill="both", expand=True)
            self.map_canvas.bind("<Configure>", lambda _e: self.draw_map())
            self.clock_overlay = tk.Frame(left, bg="#10202c", padx=6, pady=6,
                                          highlightthickness=1, highlightbackground="#4c8da0")
            self.clock_overlay.place(relx=0.12, rely=0.80, anchor="center", width=132, height=165)
            tk.Label(self.clock_overlay, text="COUNTRY TIME", bg="#10202c", fg="#80d7e8",
                     font=("Segoe UI", 8, "bold")).pack(pady=(0, 2))
            self.clock_canvas = tk.Canvas(self.clock_overlay, width=112, height=112,
                                          bg="#10202c", highlightthickness=0)
            self.clock_canvas.pack()
            self.country_clock_label = tk.Label(self.clock_overlay, text="Select a country",
                                                bg="#10202c", fg="#e6c77a",
                                                font=("Segoe UI", 8, "bold"))
            self.country_clock_label.pack(pady=(1, 0))
        self._load_map_data()

        right = tk.Frame(content, bg=self.PANEL, padx=10, pady=10, width=470)
        right.pack(side="right", fill="both", expand=True, padx=(8, 0))
        right.pack_propagate(False)
        row = tk.Frame(right, bg=self.PANEL)
        row.pack(fill="x", pady=(0, 8))
        tk.Label(row, text="STATIONS", bg=self.PANEL, fg=self.TEXT,
                 font=("Segoe UI", 10, "bold")).pack(side="left")
        self.count_label = tk.Label(row, text="Connecting…", bg=self.PANEL, fg=self.MUTED,
                                    font=("Segoe UI", 8))
        self.count_label.pack(side="right")
        self.weather_card = tk.Frame(right, bg="#1a2b32", padx=11, pady=8,
                                     highlightthickness=1, highlightbackground="#2e5960")
        self.weather_card.pack(fill="x", pady=(0, 8))
        self.weather_icon = tk.Label(self.weather_card, text="" if self._pi_lite else "◌", bg="#1a2b32", fg="#70d9ce",
                                     font=("DejaVu Sans", 11 if self._pi_lite else 23, "bold"), width=1 if self._pi_lite else 2)
        if not self._pi_lite:
            self.weather_icon.pack(side="left", padx=(0, 8))
        weather_text = tk.Frame(self.weather_card, bg="#1a2b32")
        weather_text.pack(side="left", fill="x", expand=True)
        self.weather_title = tk.Label(weather_text, text="COUNTRY WEATHER", bg="#1a2b32",
                                      fg="#a8ded6", font=("Segoe UI", 8, "bold"), anchor="w")
        self.weather_title.pack(anchor="w")
        self.weather_detail = tk.Label(weather_text, text="Select a country for current conditions",
                                       bg="#1a2b32", fg=self.TEXT, font=("Segoe UI", 10), anchor="w", justify="left")
        self.weather_detail.pack(anchor="w", pady=(2, 0))
        self.weather_source = tk.Label(weather_text, text="Open-Meteo · representative location",
                                       bg="#1a2b32", fg=self.MUTED, font=("Segoe UI", 7), anchor="w")
        self.weather_source.pack(anchor="w", pady=(2, 0))
        self.weather_metrics = {}
        if not self._pi_lite:
            metric_row = tk.Frame(self.weather_card, bg="#1a2b32")
            metric_row.pack(fill="x", pady=(8, 6))
            for key, caption, color in (("temp", "TEMP", "#ffbd59"),
                                        ("feels", "FEELS", "#ff8b67"),
                                        ("humidity", "HUMIDITY", "#64c9f0"),
                                        ("wind", "WIND", "#9cda8d")):
                tile = tk.Frame(metric_row, bg="#223b46", padx=7, pady=4)
                tile.pack(side="left", fill="x", expand=True, padx=(0, 5))
                tk.Label(tile, text=caption, bg="#223b46", fg="#9bb3bd",
                         font=("Segoe UI", 7, "bold")).pack(anchor="w")
                value = tk.Label(tile, text="—", bg="#223b46", fg=color,
                                 font=("Segoe UI", 10, "bold"))
                value.pack(anchor="w")
                self.weather_metrics[key] = value
        if not self._pi_lite:
            self.weather_ticker = tk.Canvas(self.weather_card, height=24, bg="#10202a",
                                            highlightthickness=0)
            self.weather_ticker.pack(fill="x", pady=(0, 2))
            self.weather_ticker.bind("<Configure>", self._reset_weather_ticker)
            self.weather_ticker_item = self.weather_ticker.create_text(
                8, 12, text=self.weather_ticker_message, anchor="w",
                fill="#a9e6dd", font=("Segoe UI", 8, "bold"))
        columns = ("name", "genre", "bitrate")
        self.table = ttk.Treeview(right, columns=columns, show="headings", selectmode="browse")
        for key, title in (("name", "STATION"), ("genre", "GENRE"), ("bitrate", "KBPS")):
            self.table.heading(key, text=title)
        self.table.column("name", width=210, minwidth=120)
        self.table.column("genre", width=150, minwidth=80)
        self.table.column("bitrate", width=55, minwidth=45, anchor="center")
        scroll = ttk.Scrollbar(right, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scroll.set)
        self.table.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.table.bind("<Double-1>", lambda _e: self.play_selected())
        self.table.bind("<Return>", lambda _e: self.play_selected())
        self.table.bind("<space>", lambda _e: self.play_selected())

        news_bar = tk.Frame(self, bg="#131e29", padx=10, pady=7,
                            highlightthickness=1, highlightbackground="#293d4b")
        news_tabs = tk.Frame(news_bar, bg="#131e29")
        news_tabs.pack(side="left", padx=(0, 10))
        tk.Label(news_tabs, text="NEWS", bg="#131e29", fg="#f2bd55",
                 font=("Segoe UI", 8, "bold")).pack(side="left", padx=(0, 6))
        self.news_buttons = {}
        for section in NEWS_SECTIONS:
            button = tk.Button(news_tabs, text=section, command=lambda name=section: self._select_news_section(name),
                               bg="#293a49", fg=self.TEXT, activebackground="#365166",
                               activeforeground=self.TEXT, relief="flat", bd=0, cursor="hand2",
                               padx=9, pady=4, font=("Segoe UI", 8, "bold"))
            button.pack(side="left", padx=2)
            self.news_buttons[section] = button
        self.region_choice = tk.StringVar(value="All States & UTs")
        self.region_picker = ttk.Combobox(
            news_tabs, textvariable=self.region_choice,
            values=("All States & UTs", *REGIONAL_STATES), state="readonly", width=23)
        self.region_picker.pack(side="left", padx=(7, 2))
        self.region_picker.bind("<<ComboboxSelected>>", lambda _e: self._load_regional_news())
        if self._pi_lite:
            self.news_ticker = tk.Label(news_bar, text=self.news_ticker_message, anchor="w",
                                        bg="#131e29", fg=self.TEXT,
                                        font=("DejaVu Sans", 10, "bold"), wraplength=800)
        else:
            self.news_ticker = tk.Canvas(news_bar, height=48, bg="#0e1822", highlightthickness=0)
            self.news_ticker.bind("<Configure>", self._reset_news_ticker)
            self.news_ticker_item = self.news_ticker.create_text(
                8, 12, text=self.news_ticker_message, anchor="w",
                fill="#e9f1f5", font=("Segoe UI", 25, "bold"))
        self.news_ticker.pack(side="left", fill="x", expand=True)
        self._update_news_buttons()

        foot = tk.Frame(self, bg=self.PANEL, padx=14, pady=10)
        foot.pack(fill="x", side="bottom")
        now = tk.Frame(foot, bg=self.PANEL)
        now.pack(side="left", fill="x", expand=True)
        self.now_title = tk.Label(now, text="Choose a station to start listening", bg=self.PANEL,
                                  fg=self.TEXT, font=("Segoe UI", 10, "bold"), anchor="w")
        self.now_title.pack(anchor="w")
        self.status = tk.Label(now, text="Directory powered by Radio Browser", bg=self.PANEL,
                               fg=self.MUTED, font=("Segoe UI", 8), anchor="w")
        self.status.pack(anchor="w", pady=(2, 0))
        actions = tk.Frame(foot, bg=self.PANEL)
        actions.pack(side="left", padx=10)
        self._button(actions, "▶ Play", self.play_selected, primary=True).pack(side="left", padx=2)
        self._button(actions, "Ⅱ", self.pause).pack(side="left", padx=2)
        self._button(actions, "■", self.stop).pack(side="left", padx=2)
        self._button(actions, "♥", self.toggle_favorite).pack(side="left", padx=2)
        if not self._pi_lite:
            self.audio_meter = tk.Canvas(now, width=150, height=30, bg=self.PANEL,
                                         highlightthickness=0)
            self.audio_meter.pack(side="right", padx=(8, 12))
            self.audio_meter.create_text(2, 2, text="AUDIO", anchor="nw", fill=self.MUTED,
                                         font=("Segoe UI", 7, "bold"), tags="meter-label")
        vol = tk.Frame(foot, bg=self.PANEL)
        vol.configure(width=300, height=34)
        vol.pack(side="right", padx=(8, 0))
        vol.pack_propagate(False)
        self.volume = tk.IntVar(value=75)
        tk.Label(vol, text="VOL", bg=self.PANEL, fg=self.MUTED,
                 font=("Segoe UI", 8, "bold")).pack(side="left", padx=(2, 7))
        self.volume_scale = tk.Scale(vol, from_=0, to=100, orient="horizontal",
            variable=self.volume, showvalue=False, resolution=1, length=205, width=5,
            sliderlength=15, bd=0, highlightthickness=0, relief="flat",
            bg=self.PANEL, fg=self.TEXT, troughcolor="#354653",
            activebackground="#79e1c2", command=self.set_volume)
        self.volume_scale.pack(side="left", fill="x", expand=True, padx=(0, 7))
        self.volume_bubble = tk.Label(vol, text="75%", width=4, bg="#293a49", fg=self.TEXT,
            font=("Segoe UI", 8, "bold"), padx=4, pady=3)
        self.volume_bubble.pack(side="right", padx=(0, 2))
        self._button(foot, "＋ Stream URL", self.add_stream_url).pack(side="right", padx=6)
        self._button(foot, "Load more", self.load_more).pack(side="right", padx=3)
        news_bar.pack(fill="x", side="bottom", padx=20, pady=(0, 7))

    def _load_map_data(self):
        try:
            map_file = LITE_MAP_FILE if self._pi_lite and LITE_MAP_FILE.exists() else MAP_FILE
            data = json.loads(map_file.read_text(encoding="utf-8"))
            source_features = data.get("features", [])
            self.country_shapes = source_features
            self.country_by_name = {}
            for feature in self.country_shapes:
                props = feature.get("properties", {})
                name = props.get("ADMIN") or props.get("NAME")
                code = next((value for value in (props.get("ISO_A2_EH"), props.get("ISO_A2"), props.get("ISO_A3"))
                             if value and value != "-99"), None)
                if name and code and code != "-99":
                    self.country_by_name[name] = code.upper()
                    self.country_by_code[code.upper()] = feature
            # Singapore is too small to appear in the bundled 1:110m map layer.
            if "SG" not in self.country_by_code:
                self.country_by_name["Singapore"] = "SG"
                self.country_by_code["SG"] = {
                    "type": "Feature",
                    "properties": {"ADMIN": "Singapore", "ISO_A2_EH": "SG",
                                   "LABEL_X": 103.8198, "LABEL_Y": 1.3521},
                    "geometry": {"type": "Point", "coordinates": [103.8198, 1.3521]},
                }
            self.country_picker["values"] = ["Choose a country…"] + sorted(self.country_by_name)
        except (OSError, json.JSONDecodeError):
            self.country_shapes = []
            self.map_caption.configure(text="World map file is missing")

    def load_filters(self):
        # The map replaces the country dropdown in the original app.
        return

    def draw_map(self):
        if not hasattr(self, "map_canvas") or not self.country_shapes:
            return
        canvas = self.map_canvas
        canvas.delete("mapshape")
        width, height = max(canvas.winfo_width(), 200), max(canvas.winfo_height(), 150)
        pad = 8
        map_w, map_h = width - pad * 2, height - pad * 2
        for feature in self.country_shapes:
            props = feature.get("properties", {})
            name = props.get("ADMIN") or props.get("NAME") or ""
            code = props.get("ISO_A2_EH") or props.get("ISO_A2") or props.get("ISO_A3") or ""
            if not name:
                continue
            selected = self.map_country_code and code == self.map_country_code
            fill = "#35c982" if selected else "#263e50"
            outline = "#b9ffd9" if selected else "#547184"
            geom = feature.get("geometry") or {}
            polygons = [geom.get("coordinates", [])] if geom.get("type") == "Polygon" else geom.get("coordinates", [])
            for polygon in polygons:
                if not polygon:
                    continue
                ring = polygon[0]
                points = []
                last_lon = None
                for lon, lat, *_ in ring:
                    # Avoid long cross-map edges on polygons crossing the date line.
                    if last_lon is not None and abs(lon - last_lon) > 180:
                        if len(points) >= 6:
                            self._draw_country_piece(points, name, code, fill, outline)
                        points = []
                    x = pad + (lon + 180) / 360 * map_w
                    y = pad + (82 - lat) / 164 * map_h
                    points.extend((x, y))
                    last_lon = lon
                if len(points) >= 6:
                    self._draw_country_piece(points, name, code, fill, outline)
    def _draw_country_piece(self, points, name, code, fill, outline):
        item = self.map_canvas.create_polygon(points, fill=fill, outline=outline,
                                              width=0.7, tags=("mapshape", f"country:{code}"))
        # Bind the click to the polygon itself. Canvas-level overlap queries can
        # miss filled polygon interiors on some Windows/Tk builds.
        self.map_canvas.tag_bind(item, "<Button-1>",
            lambda _event, country=name, country_code=code:
                self.select_map_country(country, country_code))
        self.map_canvas.tag_bind(item, "<Enter>",
            lambda _event: self.map_canvas.configure(cursor="hand2"))
        self.map_canvas.tag_bind(item, "<Leave>",
            lambda _event: self.map_canvas.configure(cursor="hand2"))

    def _country_at_click(self, event):
        hits = self.map_canvas.find_overlapping(event.x - 1, event.y - 1, event.x + 1, event.y + 1)
        for item in reversed(hits):
            tags = self.map_canvas.gettags(item)
            code_tag = next((tag for tag in tags if tag.startswith("country:")), None)
            if code_tag:
                code = code_tag.split(":", 1)[1]
                feature = next((f for f in self.country_shapes
                                if (f.get("properties", {}).get("ISO_A2_EH")
                                    or f.get("properties", {}).get("ISO_A2")
                                    or f.get("properties", {}).get("ISO_A3")) == code), None)
                if feature:
                    props = feature["properties"]
                    name = props.get("ADMIN") or props.get("NAME") or code
                    self.select_map_country(name, code)
                return

    def _country_picker_selected(self, _event=None):
        name = self.country_choice.get()
        code = self.country_by_name.get(name)
        if code:
            self.select_map_country(name, code)

    def select_map_country(self, name, code):
        self.map_country_name, self.map_country_code = name, code
        self.country_choice.set(name)
        self.map_caption.configure(text=f"COUNTRY  ·  {name}" if self._pi_lite else f"WORLD MAP  ·  {name}")
        self._set_wave_center(code)
        self._load_weather(name, code)
        self.country_time_name = name
        self.country_timezone = None
        self.country_utc_offset_seconds = None
        self.country_timezone_status = "loading"
        self.country_clock_label.configure(text=f"{name} · loading time zone…")
        self.draw_map()
        self.search_directory()

    def _set_wave_center(self, code):
        feature = self.country_by_code.get((code or "").upper())
        props = feature.get("properties", {}) if feature else {}
        try:
            self.wave_center = (float(props["LABEL_X"]), float(props["LABEL_Y"]))
        except (KeyError, TypeError, ValueError):
            self.wave_center = None

    def _animate_waves(self):
        if self._radio_suspended:
            return
        if hasattr(self, "map_canvas"):
            canvas = self.map_canvas
            canvas.delete("signalwave")
            if self.wave_center:
                width, height = max(canvas.winfo_width(), 200), max(canvas.winfo_height(), 150)
                lon, lat = self.wave_center
                cx = 8 + (lon + 180) / 360 * (width - 16)
                cy = 8 + (82 - lat) / 164 * (height - 16)
                colors = ("#7be8d2", "#54cbb7", "#398f88")
                for i, color in enumerate(colors):
                    radius = 5 + ((self.wave_phase + i * 12) % 36)
                    canvas.create_oval(cx-radius, cy-radius, cx+radius, cy+radius,
                                       outline=color, width=2, tags="signalwave")
                canvas.create_oval(cx-3, cy-3, cx+3, cy+3,
                                   fill="#ffe08a", outline="", tags="signalwave")
                canvas.tag_raise("signalwave")
                self.wave_phase = (self.wave_phase + 3) % 36
        self.after(self._wave_interval, self._animate_waves)

    def _tick_clock(self):
        if self._radio_suspended:
            return
        try:
            if self.country_timezone_status == "ready" and self.country_timezone:
                now = datetime.now(ZoneInfo(self.country_timezone))
            elif self.country_timezone_status == "ready" and self.country_utc_offset_seconds is not None:
                now = datetime.now(timezone(timedelta(seconds=self.country_utc_offset_seconds)))
            else:
                now = datetime.now().astimezone()
        except (ZoneInfoNotFoundError, ValueError):
            offset = self.country_utc_offset_seconds
            now = (datetime.now(timezone(timedelta(seconds=offset))) if offset is not None
                   else datetime.now().astimezone())
        if hasattr(self, "clock_label"):
            tag = self.map_country_code if self.country_timezone_status == "ready" else "LOCAL"
            self.clock_label.configure(text=f"{tag}  {now:%H:%M:%S}")
        if hasattr(self, "country_clock_label"):
            if not self.country_time_name:
                label = f"LOCAL TIME  ·  {now:%H:%M:%S}"
            elif self.country_timezone_status == "ready":
                label = f"{self.country_time_name[:16].upper()}  ·  {now:%H:%M:%S}"
            elif self.country_timezone_status == "loading":
                label = f"{self.country_time_name[:16]} · loading time zone…"
            else:
                label = f"{self.country_time_name[:16]} · time zone unavailable"
            self.country_clock_label.configure(text=label)
        if hasattr(self, "clock_canvas"):
            self._draw_analog_clock(now)
        self.after(1000, self._tick_clock)

    def _draw_analog_clock(self, now):
        canvas = self.clock_canvas
        canvas.delete("clock")
        width = max(112, canvas.winfo_width())
        height = max(112, canvas.winfo_height())
        cx, cy = width / 2, height / 2
        radius = min(width, height) / 2 - 5
        canvas.create_oval(cx-radius, cy-radius, cx+radius, cy+radius,
                           fill="#182f3d", outline="#65cddd", width=2, tags="clock")
        for tick in range(60):
            angle = math.radians(tick * 6 - 90)
            major = tick % 5 == 0
            inner = radius - (10 if major else 4)
            canvas.create_line(cx + inner * math.cos(angle), cy + inner * math.sin(angle),
                               cx + radius * math.cos(angle), cy + radius * math.sin(angle),
                               fill="#d9f3f4" if major else "#668491",
                               width=2 if major else 1, tags="clock")
        second = now.second
        minute = now.minute + second / 60
        hour = (now.hour % 12) + minute / 60
        for value, degrees, length, color, weight in (
                (hour, 30, radius * 0.48, "#f5ca74", 4),
                (minute, 6, radius * 0.70, "#eaf6f5", 3),
                (second, 6, radius * 0.80, "#ff7e73", 1)):
            angle = math.radians(value * degrees - 90)
            canvas.create_line(cx, cy, cx + length * math.cos(angle), cy + length * math.sin(angle),
                               fill=color, width=weight, capstyle="round", tags="clock")
        canvas.create_oval(cx-3, cy-3, cx+3, cy+3, fill="#fff1bd", outline="", tags="clock")

    def _load_news_feeds(self):
        if self._pi_lite:
            self._start_news_request("WORLD", NEWS_FEEDS["WORLD"])
            return
        for section, url in NEWS_FEEDS.items():
            self._start_news_request(section, url)
        self._load_regional_news()

    def _start_news_request(self, section, url):
        request_id = self.news_request_ids.get(section, 0) + 1
        self.news_request_ids[section] = request_id
        threading.Thread(target=self._fetch_news_feed, args=(section, url, request_id), daemon=True).start()

    def _load_regional_news(self):
        if not hasattr(self, "region_choice"):
            return
        selected = self.region_choice.get()
        if selected == "All States & UTs":
            state_terms = " OR ".join(f'"{state}"' for state in REGIONAL_STATES)
            query = f"({state_terms}) India regional news"
        else:
            query = f'"{selected}" India news'
        params = urllib.parse.urlencode({"q": query, "hl": "en-IN", "gl": "IN", "ceid": "IN:en"})
        url = "https://news.google.com/rss/search?" + params
        self.news_headlines.pop("REGIONAL INDIA", None)
        if self.news_section == "REGIONAL INDIA":
            self.news_ticker_message = f"Loading {selected} regional headlines…"
            self._reset_news_ticker()
        self._start_news_request("REGIONAL INDIA", url)

    def _fetch_news_feed(self, section, url, request_id):
        try:
            request = urllib.request.Request(url, headers={
                "User-Agent": "SURAKMediaCenter/1.0 (RSS headlines)",
                "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml",
            })
            with urllib.request.urlopen(request, timeout=18) as response:
                payload = response.read(2_000_000)
            root = ET.fromstring(payload)
            entries = [node for node in root.iter()
                       if node.tag.rsplit("}", 1)[-1].lower() in ("item", "entry")]
            headlines = []
            for entry in entries:
                title_node = next((node for node in entry if node.tag.rsplit("}", 1)[-1].lower() == "title"), None)
                title = " ".join("".join(title_node.itertext()).split()) if title_node is not None else ""
                if title:
                    headlines.append(html.unescape(title))
                if len(headlines) >= 15:
                    break
            if not headlines:
                raise ValueError("No headlines in feed")
            self.news_events.put((section, request_id, headlines, None))
        except Exception as exc:
            self.news_events.put((section, request_id, [], str(exc)))

    def _drain_news_events(self):
        if self._radio_suspended:
            return
        try:
            while True:
                section, request_id, headlines, error = self.news_events.get_nowait()
                if request_id != self.news_request_ids.get(section):
                    continue
                if error:
                    self.news_headlines[section] = f"{section.title()} headlines unavailable · check internet and retry"
                else:
                    self.news_headlines[section] = "     ✦     ".join(headlines) + "     ✦     "
                if section == self.news_section:
                    self.news_ticker_message = self.news_headlines[section]
                    self._reset_news_ticker()
        except queue.Empty:
            pass
        self.after(self._data_poll_interval, self._drain_news_events)

    def _select_news_section(self, section):
        self.news_section = section
        self.region_picker.pack_forget()
        if section == "REGIONAL INDIA":
            self.region_picker.pack(side="left", padx=(7, 2))
            self.news_ticker_message = f"Loading {self.region_choice.get()} regional headlines…"
            self._load_regional_news()
        else:
            if section not in self.news_headlines and section in NEWS_FEEDS:
                self._start_news_request(section, NEWS_FEEDS[section])
            self.news_ticker_message = self.news_headlines.get(section, f"Loading {section.title()} headlines…")
        self._update_news_buttons()
        self._reset_news_ticker()

    def _update_news_buttons(self):
        for section, button in getattr(self, "news_buttons", {}).items():
            button.configure(bg="#a66b16" if section == self.news_section else "#293a49")

    def _reset_news_ticker(self, _event=None):
        if not hasattr(self, "news_ticker") or not self.news_ticker.winfo_exists():
            return
        if self._pi_lite:
            self.news_ticker.configure(text=self.news_ticker_message)
            return
        self.news_ticker_x = max(120, self.news_ticker.winfo_width())
        self.news_ticker.coords(self.news_ticker_item, self.news_ticker_x, 24)
        self.news_ticker.itemconfigure(self.news_ticker_item, text=self.news_ticker_message)

    def _tick_news_ticker(self):
        if self._pi_lite:
            return
        if self._radio_suspended:
            return
        if hasattr(self, "news_ticker") and self.news_ticker.winfo_exists():
            self.news_ticker_x -= 2
            bbox = self.news_ticker.bbox(self.news_ticker_item)
            if bbox and bbox[2] < 0:
                self.news_ticker_x = max(120, self.news_ticker.winfo_width())
            self.news_ticker.coords(self.news_ticker_item, self.news_ticker_x, 24)
        self.after(self._ticker_interval, self._tick_news_ticker)

    def _load_weather(self, name, code):
        feature = self.country_by_code.get((code or "").upper())
        props = feature.get("properties", {}) if feature else {}
        try:
            lat, lon = float(props["LABEL_Y"]), float(props["LABEL_X"])
        except (KeyError, TypeError, ValueError):
            self.weather_title.configure(text=f"WEATHER  ·  {name.upper()}")
            self.weather_detail.configure(text="Weather location unavailable")
            self.weather_icon.configure(text="—")
            self.country_timezone_status = "unavailable"
            return
        self.weather_title.configure(text=f"WEATHER  ·  {name.upper()}")
        self.weather_detail.configure(text="Getting current conditions…")
        self.weather_icon.configure(text="◌")

        def fetch():
            params = {
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
                "hourly": "temperature_2m,precipitation_probability,weather_code",
                "forecast_days": 1,
                "timezone": "auto",
            }
            url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(params)
            request = urllib.request.Request(url, headers={"User-Agent": "WorldRadioTk/1.0"})
            try:
                with urllib.request.urlopen(request, timeout=15) as response:
                    data = json.loads(response.read().decode("utf-8"))
                self.weather_events.put((name, data, None))
            except Exception as exc:
                self.weather_events.put((name, None, str(exc)))

        threading.Thread(target=fetch, daemon=True).start()

    def _drain_weather_events(self):
        if self._radio_suspended:
            return
        try:
            while True:
                name, data, error = self.weather_events.get_nowait()
                if name != self.map_country_name:
                    continue
                if error or not data:
                    self.weather_icon.configure(text="—")
                    self.weather_detail.configure(text="Weather unavailable · check internet")
                    self.country_timezone_status = "unavailable"
                    continue
                self.country_timezone = data.get("timezone") or None
                self.country_utc_offset_seconds = data.get("utc_offset_seconds")
                self.country_timezone_status = ("ready" if self.country_timezone or
                                                self.country_utc_offset_seconds is not None
                                                else "unavailable")
                current = data.get("current", {})
                icon, description = self._weather_description(int(current.get("weather_code", -1)))
                temp = current.get("temperature_2m", "—")
                feels = current.get("apparent_temperature")
                humidity = current.get("relative_humidity_2m", "—")
                wind = current.get("wind_speed_10m", "—")
                code = int(current.get("weather_code", -1))
                self.weather_color = self._weather_color(code)
                feels_text = f"  Feels {feels:g}°" if isinstance(feels, (float, int)) else ""
                self.weather_icon.configure(text=icon)
                if not self._pi_lite:
                    self.weather_card.configure(highlightbackground=self.weather_color)
                self.weather_detail.configure(
                    text=f"{temp}°C  ·  {description}{feels_text}\nHumidity {humidity}%  ·  Wind {wind} km/h")
                self.weather_source.configure(text="Current conditions · representative country point · Open-Meteo")
                if not self._pi_lite:
                    self.weather_metrics["temp"].configure(text=f"{temp}°C")
                    self.weather_metrics["feels"].configure(text=f"{feels}°C" if feels is not None else "—")
                    self.weather_metrics["humidity"].configure(text=f"{humidity}%")
                    self.weather_metrics["wind"].configure(text=f"{wind} km/h")
                    self.weather_ticker_message = self._make_weather_ticker(name, data, description, temp)
                    self._reset_weather_ticker()
                self.draw_map()
        except queue.Empty:
            pass
        self.after(self._data_poll_interval, self._drain_weather_events)

    @staticmethod
    def _weather_description(code):
        if code == 0: return "☀", "Clear"
        if code in (1, 2): return "⛅", "Partly cloudy"
        if code == 3: return "☁", "Overcast"
        if code in (45, 48): return "≋", "Fog"
        if code in (51, 53, 55, 56, 57): return "☂", "Drizzle"
        if code in (61, 63, 65, 66, 67, 80, 81, 82): return "☂", "Rain"
        if code in (71, 73, 75, 77, 85, 86): return "❄", "Snow"
        if code in (95, 96, 99): return "ϟ", "Thunderstorm"
        return "◌", "Conditions unavailable"

    @staticmethod
    def _weather_color(code):
        if code == 0:
            return "#f5bd4f"
        if code in (1, 2, 3):
            return "#55bde8"
        if code in (45, 48):
            return "#aebec8"
        if code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82):
            return "#568cf5"
        if code in (71, 73, 75, 77, 85, 86):
            return "#bceaff"
        if code in (95, 96, 99):
            return "#c47cf2"
        return "#47c98b"

    @classmethod
    def _make_weather_ticker(cls, name, data, description, temperature):
        parts = [f"{name}  {temperature}°C  {description}"]
        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        temps = hourly.get("temperature_2m", [])
        rain = hourly.get("precipitation_probability", [])
        current_time = data.get("current", {}).get("time", "")
        start = next((i for i, value in enumerate(times) if value >= current_time), 0)
        for i in range(start + 1, min(start + 7, len(times), len(temps))):
            label = times[i][-5:] if len(times[i]) >= 5 else times[i]
            rain_pct = rain[i] if i < len(rain) else "—"
            parts.append(f"{label}  {temps[i]}°  rain {rain_pct}%")
        return "     ✦     ".join(parts) + "     ✦     "

    def _reset_weather_ticker(self, _event=None):
        if self._pi_lite:
            return
        if not hasattr(self, "weather_ticker") or not self.weather_ticker.winfo_exists():
            return
        width = max(120, self.weather_ticker.winfo_width())
        self.weather_ticker.coords(self.weather_ticker_item, width, 12)
        self.weather_ticker.itemconfigure(self.weather_ticker_item, text=self.weather_ticker_message)
        self.weather_ticker_x = width

    def _tick_weather_ticker(self):
        if self._pi_lite:
            return
        if self._radio_suspended:
            return
        if hasattr(self, "weather_ticker") and self.weather_ticker.winfo_exists():
            width = max(120, self.weather_ticker.winfo_width())
            self.weather_ticker_x -= 2
            bbox = self.weather_ticker.bbox(self.weather_ticker_item)
            if bbox and bbox[2] < 0:
                self.weather_ticker_x = width
            self.weather_ticker.coords(self.weather_ticker_item, self.weather_ticker_x, 12)
        self.after(self._ticker_interval, self._tick_weather_ticker)

    def clear_map_selection(self):
        self.map_country_code = self.map_country_name = None
        self.wave_center = None
        self.country_time_name = None
        self.country_timezone = None
        self.country_utc_offset_seconds = None
        self.country_timezone_status = "local"
        self.country_clock_label.configure(text="LOCAL TIME")
        self.country_choice.set("Choose a country…")
        self.map_caption.configure(text="COUNTRY  ·  Select a country" if self._pi_lite else "WORLD MAP  ·  Select a country")
        self.weather_title.configure(text="COUNTRY WEATHER")
        self.weather_icon.configure(text="◌")
        self.weather_detail.configure(text="Select a country for current conditions")
        self.weather_source.configure(text="Open-Meteo · representative location")
        self.weather_color = "#47c98b"
        for metric in self.weather_metrics.values():
            metric.configure(text="—")
        self.weather_ticker_message = "Select a country to see local weather and the next hours"
        self._reset_weather_ticker()
        self.draw_map()
        self.search_directory()

    def load_directory(self):
        if getattr(self, "_default_country_pending", False):
            self._default_country_pending = False
            india_name = next((name for name, code in self.country_by_name.items()
                               if code == "IN"), "India")
            self.select_map_country(india_name, "IN")
            return
        if hasattr(self, "map_country_code"):
            self.map_country_code = self.map_country_name = None
            self.wave_center = None
            self.country_time_name = None
            self.country_timezone = None
            self.country_utc_offset_seconds = None
            self.country_timezone_status = "local"
            self.country_clock_label.configure(text="LOCAL TIME")
            if hasattr(self, "country_choice"):
                self.country_choice.set("Choose a country…")
                self.map_caption.configure(text="COUNTRY  ·  Select a country" if self._pi_lite else "WORLD MAP  ·  Select a country")
                self.weather_title.configure(text="COUNTRY WEATHER")
                self.weather_icon.configure(text="◌")
                self.weather_detail.configure(text="Select a country for current conditions")
                self.weather_source.configure(text="Open-Meteo · representative location")
                self.weather_color = "#47c98b"
                for metric in self.weather_metrics.values():
                    metric.configure(text="—")
                self.weather_ticker_message = "Select a country to see local weather and the next hours"
                self._reset_weather_ticker()
                self.draw_map()
        source = self.source_var.get() if hasattr(self, "source_var") else RADIO_SOURCES[0]
        if source == "IPRD":
            self._load_iprd_catalog(all_countries=True)
            return
        if source == "Verified Radio":
            self._load_verified_stations(all_countries=True)
            return
        super().load_directory()

    def _animate_audio_meter(self):
        if self._pi_lite:
            return
        if self._radio_suspended or not hasattr(self, "audio_meter"):
            return
        canvas = self.audio_meter
        canvas.delete("meter-bar")
        try:
            playing = bool(self.player and self.player.is_playing())
        except Exception:
            playing = False
        width = max(100, canvas.winfo_width())
        height = max(24, canvas.winfo_height())
        bars = 16
        gap = 3
        bar_width = max(3, (width - (bars - 1) * gap - 8) / bars)
        colors = ("#42d392", "#55d99b", "#77d784", "#add363", "#e0c45a", "#eea452")
        self.meter_phase += 0.28
        baseline = height - 3
        available = height - 14
        for index in range(bars):
            wave = (math.sin(self.meter_phase + index * 0.73) +
                    0.45 * math.sin(self.meter_phase * 1.7 + index * 1.19))
            level = (0.12 + 0.78 * abs(wave)) if playing else 0.06
            bar_height = max(2, available * level)
            x1 = 4 + index * (bar_width + gap)
            canvas.create_rectangle(x1, baseline - bar_height, x1 + bar_width, baseline,
                                    fill=colors[min(len(colors) - 1,
                                                    int(level * len(colors)))],
                                    outline="", tags="meter-bar")
        self.after(self._meter_interval, self._animate_audio_meter)

    def search_directory(self):
        self.only_favorites = False
        self.offset = 0
        term = self.search.get().strip()
        if term.startswith("Search all stations"):
            term = ""
        source = self.source_var.get() if hasattr(self, "source_var") else RADIO_SOURCES[0]
        if source == "IPRD":
            self._load_iprd_catalog(all_countries=False)
            return
        if source == "Verified Radio":
            self._load_verified_stations(all_countries=False)
            return
        params = {"limit": PAGE_SIZE, "offset": 0, "order": "clickcount",
                  "reverse": "true", "hidebroken": "true"}
        if term:
            params["name"] = term
        if self.map_country_code:
            params["countrycode"] = self.map_country_code
        self.async_call(lambda: api_get("/stations/search", params), self._directory_loaded,
                        "Searching stations…")

    def _source_changed(self, _event=None):
        selected_source = self.source_var.get()
        def reload_when_idle():
            if not self.winfo_exists() or self.source_var.get() != selected_source:
                return
            if self.loading:
                self.after(250, reload_when_idle)
                return
            self.search_directory()
        if self.loading:
            self.after(250, reload_when_idle)
        else:
            self.search_directory()

    @staticmethod
    def _fetch_json(url):
        request = urllib.request.Request(url, headers={
            "User-Agent": "SURAKMediaCenter/1.0 (radio directory)",
            "Accept": "application/json",
        })
        with urllib.request.urlopen(request, timeout=35) as response:
            return json.loads(response.read(16_000_000).decode("utf-8"))

    @staticmethod
    def _external_station(provider, key, name, country, stream, tags="", codec="", bitrate=0,
                          clickcount=0):
        stream = str(stream or "").strip()
        if not stream.startswith(("http://", "https://")):
            return None
        return {
            "stationuuid": f"{provider}:{key or stream}",
            "name": str(name or "Untitled station").strip(),
            "url": stream,
            "url_resolved": stream,
            "country": str(country or ""),
            "tags": str(tags or ""),
            "codec": str(codec or ""),
            "bitrate": int(bitrate or 0) if str(bitrate or "0").isdigit() else 0,
            "clickcount": int(clickcount or 0) if str(clickcount or "0").isdigit() else 0,
        }

    def _load_iprd_catalog(self, all_countries=False):
        if self.iprd_catalog is not None:
            self._show_iprd_stations(all_countries)
            return
        self.async_call(lambda: self._fetch_json(IPRD_CATALOG_URL),
                        lambda catalog: self._iprd_catalog_loaded(catalog, all_countries),
                        "Loading IPRD station directory…")

    def _iprd_catalog_loaded(self, catalog, all_countries):
        stations = catalog.get("stations", []) if isinstance(catalog, dict) else []
        self.iprd_catalog = []
        for item in stations:
            streams = item.get("streams") or []
            if isinstance(streams, dict):
                streams = [streams]
            if not streams:
                continue
            def reliability(entry):
                try:
                    return float(entry.get("reliability") or 0)
                except (TypeError, ValueError):
                    return 0.0
            stream_data = max(streams, key=reliability)
            genres = item.get("genres") or []
            tags = item.get("tags") or []
            languages = item.get("language") or []
            genres = [genres] if isinstance(genres, str) else genres
            tags = [tags] if isinstance(tags, str) else tags
            languages = [languages] if isinstance(languages, str) else languages
            station = self._external_station(
                "iprd", item.get("id"), item.get("name"), item.get("country"),
                stream_data.get("url"), ", ".join(str(v) for v in (*genres, *tags, *languages)),
                stream_data.get("format"), stream_data.get("bitrate", 0))
            if station:
                self.iprd_catalog.append(station)
        self._show_iprd_stations(all_countries)

    def _show_iprd_stations(self, all_countries=False):
        self._show_external_stations(self.iprd_catalog or [], "IPRD", all_countries)

    def _load_verified_stations(self, all_countries=False):
        if not all_countries and self.map_country_code:
            code = self.map_country_code.upper()
            cached = self.verified_country_cache.get(code)
            if cached is not None:
                self._show_external_stations(cached, "Verified Radio", False)
                return
            url = f"{VERIFIED_RAW_BASE}/stations/{urllib.parse.quote(code)}.json"
            self.async_call(lambda: self._fetch_json(url),
                lambda payload: self._verified_country_loaded(code, payload),
                f"Loading verified {self.map_country_name or code} stations…")
            return
        if self.verified_all_cache is not None:
            self._show_external_stations(self.verified_all_cache, "Verified Radio", True)
            return
        def fetch_all():
            request = urllib.request.Request(VERIFIED_ALL_M3U_URL,
                headers={"User-Agent": "SURAKMediaCenter/1.0 (verified radio playlist)"})
            with urllib.request.urlopen(request, timeout=40) as response:
                text = response.read(12_000_000).decode("utf-8-sig", errors="replace")
            return self._parse_verified_m3u(text)
        self.async_call(fetch_all, self._verified_all_loaded,
                        "Loading verified worldwide radio stations…")

    def _verified_country_loaded(self, code, payload):
        country = payload.get("country", self.map_country_name or code)
        rows = []
        for item in payload.get("stations", []):
            genres = item.get("genre") or []
            languages = item.get("langs") or []
            if isinstance(genres, str): genres = [genres]
            if isinstance(languages, str): languages = [languages]
            station = self._external_station(
                "verified", f"{code}:{item.get('id')}", item.get("name"), country,
                item.get("stream"), ", ".join(str(v) for v in (*genres, *languages)),
                item.get("codec"), item.get("bitrate", 0), item.get("clicks", 0))
            if station:
                rows.append(station)
        self.verified_country_cache[code] = rows
        self._show_external_stations(rows, "Verified Radio", False)

    def _verified_all_loaded(self, rows):
        self.verified_all_cache = rows
        self._show_external_stations(rows, "Verified Radio", True)

    @staticmethod
    def _parse_verified_m3u(text):
        rows = []
        metadata = ""
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("#EXTINF:"):
                metadata = line
                continue
            if not line or line.startswith("#") or not metadata:
                continue
            title = metadata.split(",", 1)[1].strip() if "," in metadata else line
            group = re.search(r'group-title="([^"]*)"', metadata)
            genre = re.search(r'tvg-genre="([^"]*)"', metadata)
            country = group.group(1) if group else ""
            tags = genre.group(1).replace(",", ", ") if genre else ""
            station = WorldRadioMap._external_station(
                "verified", line, title, country, line, tags)
            if station:
                rows.append(station)
            metadata = ""
        return rows

    def _show_external_stations(self, stations, source, all_countries):
        term = self.search.get().strip().casefold()
        if term.startswith("search all stations"):
            term = ""
        country_aliases = set()
        if not all_countries and self.map_country_name:
            country_aliases.add(self.map_country_name.casefold())
            aliases = {
                "US": ("United States", "United States of America"),
                "KR": ("South Korea", "Republic of Korea"),
                "KP": ("North Korea", "Democratic People's Republic of Korea"),
                "RU": ("Russia", "Russian Federation"),
                "GB": ("United Kingdom", "Great Britain"),
                "IR": ("Iran", "Iran, Islamic Republic of"),
                "VN": ("Vietnam", "Viet Nam"),
                "BO": ("Bolivia", "Bolivia, Plurinational State of"),
                "TZ": ("Tanzania", "Tanzania, United Republic of"),
                "CD": ("Democratic Republic of the Congo", "Congo, The Democratic Republic of the"),
                "CG": ("Republic of the Congo", "Congo"),
            }
            country_aliases.update(value.casefold() for value in
                                   aliases.get(self.map_country_code, ()))
        rows = [station for station in stations
                if (not country_aliases or station.get("country", "").casefold() in country_aliases)
                and (not term or term in station.get("name", "").casefold()
                     or term in station.get("tags", "").casefold())]
        self.only_favorites = False
        self.stations = rows
        self.offset = len(rows)
        self.total_hint = len(rows)
        self.render()
        self.set_status(f"{source} · {len(rows):,} stations" +
                         (f" · {self.map_country_name}" if country_aliases else " · Worldwide"))

    def load_more(self):
        if getattr(self, "source_var", None) and self.source_var.get() != RADIO_SOURCES[0]:
            self.set_status("All stations from this source are loaded.")
            return
        if self.only_favorites or self.loading:
            return
        params = {"limit": PAGE_SIZE, "offset": self.offset, "order": "clickcount",
                  "reverse": "true", "hidebroken": "true"}
        term = self.search.get().strip()
        if term and not term.startswith("Search all stations"):
            params["name"] = term
        if self.map_country_code:
            params["countrycode"] = self.map_country_code
        self.async_call(lambda: api_get("/stations/search", params), self._more_loaded,
                        "Loading more stations…")

    def render(self):
        rows = list(self.stations)
        for item in self.table.get_children():
            self.table.delete(item)
        for station in rows:
            name = (station.get("name") or "Untitled station").strip()
            if self.current and station_id(station) == station_id(self.current):
                name = "▶ " + name
            self.table.insert("", "end", iid=str(hash(station_id(station))), values=(
                name, (station.get("tags") or "—")[:25], station.get("bitrate", 0) or "—"))
        self._row_stations = {str(hash(station_id(station))): station for station in rows}
        label = f"{len(rows):,} stations"
        if self.map_country_name and not self.only_favorites:
            label += f" · {self.map_country_name}"
        elif self.only_favorites:
            label += " · Favorites"
        self.count_label.configure(text=label)


if __name__ == "__main__":
    app = WorldRadioMap()
    app.root.mainloop()
