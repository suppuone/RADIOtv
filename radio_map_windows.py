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
from concurrent.futures import ThreadPoolExecutor, as_completed
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from PIL import Image, ImageDraw, ImageFilter, ImageTk

from radio_app import WorldRadio, api_get, station_id, PAGE_SIZE

APP_DIR = Path(__file__).resolve().parent
MAP_FILE = APP_DIR / "countries.geojson"
LITE_MAP_FILE = APP_DIR / "countries_lite.json"
FAVORITES_FILE = APP_DIR / "map_favorites.json"
IPRD_CATALOG_URL = "https://iprd-org.github.io/iprd/site_data/metadata/catalog.json"
VERIFIED_RAW_BASE = "https://raw.githubusercontent.com/eyalev/verified-radio-streams/main"
VERIFIED_INDEX_URL = VERIFIED_RAW_BASE + "/stations/index.json"
VERIFIED_ALL_M3U_URL = VERIFIED_RAW_BASE + "/m3u/all.m3u"
RADIO_SOURCES = ("Radio Browser", "IPRD", "Verified Radio", "Akashvani", "BBC", "Mediacorp", "SouthRadios")
SOUTHRADIOS_STATION_NAMES = (
    "Ajith Radio", "Vijay Radio", "Thala Thalapathy Radio", "Tamil Pop Radio",
    "Ilayamaan Radio", "Ilayamaan Lite Radio", "K J Yesudas Radio", "Anirudh Radio",
    "Yuvan Shankar Raja Radio", "D Imman Radio", "Harris Jayaraj Radio", "Tamil Lite Radio",
)
AKASHVANI_STATIONS_URL = "https://raw.githubusercontent.com/codito/akashvani/master/stations.json"
BBC_STATIONS = (
    ("BBC Radio 1", "bbc_radio_one", "https://as-hls-ww-live.akamaized.net/pool_01505109/live/ww/bbc_radio_one/bbc_radio_one.isml/bbc_radio_one-audio=96000.norewind.m3u8", "Pop"),
    ("BBC Radio 1Xtra", "bbc_1xtra", "https://as-hls-ww-live.akamaized.net/pool_92079267/live/ww/bbc_1xtra/bbc_1xtra.isml/bbc_1xtra-audio=96000.norewind.m3u8", "Urban music"),
    ("BBC Radio 2", "bbc_radio_two", "https://as-hls-ww-live.akamaized.net/pool_74208725/live/ww/bbc_radio_two/bbc_radio_two.isml/bbc_radio_two-audio=96000.norewind.m3u8", "Music"),
    ("BBC Radio 3", "bbc_radio_three", "https://as-hls-ww-live.akamaized.net/pool_23461179/live/ww/bbc_radio_three/bbc_radio_three.isml/bbc_radio_three-audio=96000.norewind.m3u8", "Classical"),
    ("BBC Radio 4", "bbc_radio_fourfm", "https://as-hls-ww-live.akamaized.net/pool_55057080/live/ww/bbc_radio_fourfm/bbc_radio_fourfm.isml/bbc_radio_fourfm-audio=96000.norewind.m3u8", "News and speech"),
    ("BBC Radio 4 Extra", "bbc_radio_four_extra", "https://as-hls-ww-live.akamaized.net/pool_26173715/live/ww/bbc_radio_four_extra/bbc_radio_four_extra.isml/bbc_radio_four_extra-audio=96000.norewind.m3u8", "Comedy and drama"),
    ("BBC Radio 5 Live", "bbc_radio_five_live", "https://as-hls-ww-live.akamaized.net/pool_89021708/live/ww/bbc_radio_five_live/bbc_radio_five_live.isml/bbc_radio_five_live-audio=96000.norewind.m3u8", "News and sport"),
    ("BBC Radio 6 Music", "bbc_6music", "https://as-hls-ww-live.akamaized.net/pool_81827798/live/ww/bbc_6music/bbc_6music.isml/bbc_6music-audio=96000.norewind.m3u8", "Alternative music"),
    ("BBC Asian Network", "bbc_asian_network", "https://as-hls-ww-live.akamaized.net/pool_22108647/live/ww/bbc_asian_network/bbc_asian_network.isml/bbc_asian_network-audio=96000.norewind.m3u8", "Asian music and speech"),
    ("BBC World Service", "bbc_world_service", "https://as-hls-ww-live.akamaized.net/pool_87948813/live/ww/bbc_world_service/bbc_world_service.isml/bbc_world_service-audio=96000.norewind.m3u8", "World news"),
    ("BBC Radio Scotland", "bbc_radio_scotland_fm", "https://as-hls-ww-live.akamaized.net/pool_43322914/live/ww/bbc_radio_scotland_fm/bbc_radio_scotland_fm.isml/bbc_radio_scotland_fm-audio=96000.norewind.m3u8", "Scotland"),
    ("BBC Radio Wales", "bbc_radio_wales_fm", "https://as-hls-ww-live.akamaized.net/pool_97517794/live/ww/bbc_radio_wales_fm/bbc_radio_wales_fm.isml/bbc_radio_wales_fm-audio=96000.norewind.m3u8", "Wales"),
    ("BBC Radio Ulster", "bbc_radio_ulster", "https://as-hls-ww-live.akamaized.net/pool_31244774/live/ww/bbc_radio_ulster/bbc_radio_ulster.isml/bbc_radio_ulster-audio=96000.norewind.m3u8", "Northern Ireland"),
    ("BBC Radio Cymru", "bbc_radio_cymru", "https://as-hls-ww-live.akamaized.net/pool_24792333/live/ww/bbc_radio_cymru/bbc_radio_cymru.isml/bbc_radio_cymru-audio=96000.norewind.m3u8", "Welsh language"),
)
MEDIACORP_STATIONS = (
    ("CLASS 95", "CLASS95AAC", "English · Pop"),
    ("GOLD 905", "GOLD905AAC", "English · Classic hits"),
    ("987", "987FMAAC", "English · Pop"),
    ("CNA938", "938NOWAAC", "English · News and talk"),
    ("Symphony 924", "SYMPHONY924AAC", "English · Classical"),
    ("YES 933", "YES933AAC", "Mandarin · Pop"),
    ("LOVE 972", "LOVE972FMAAC", "Mandarin · Music and lifestyle"),
    ("CAPITAL 958", "CAPITAL958FMAAC", "Mandarin · News and infotainment"),
    ("RIA 897", "RIA897FMAAC", "Malay · Music"),
    ("WARNA 942", "WARNA942FMAAC", "Malay · News and infotainment"),
    ("OLI 968", "OLI968FMAAC", "Tamil · News and entertainment"),
    ("indiego", "INDIEGO_S01AAC_48", "English · Indie · Digital"),
)
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

    def _button(self, parent, label, command, primary=False):
        button = super()._button(parent, label, command, primary=primary)
        button.configure(font=("Segoe UI", 12, "bold" if primary else "normal"))
        return button

    def __init__(self, master=None):
        self._pi_lite = os.environ.get("SURAK_PI_LITE") == "1"
        self._ticker_interval = 110 if self._pi_lite else 45
        self._meter_interval = 220 if self._pi_lite else 100
        self._data_poll_interval = 500 if self._pi_lite else 160
        self._radio_suspended = False
        self._radio_after_ids = set()
        self.favorite_tuner_index = 0
        self._panel_glow_job = None
        self._panel_glow_photo = None
        self._panel_glow_item = None
        self._tuner_static_glow_photo = None
        self._tuner_static_glow_item = None
        self._default_country_pending = True
        self.meter_phase = 0.0
        self.iprd_catalog = None
        self.akashvani_catalog = None
        self.bbc_catalog = None
        self.mediacorp_catalog = None
        self.southradios_catalog = None
        self.verified_country_cache = {}
        self.verified_all_cache = None
        self.country_shapes = []
        self.country_by_name = {}
        self.country_by_code = {}
        self.map_country_code = None
        self.map_country_name = None
        self._map_drawn_selected_code = None
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
        self.after(self._data_poll_interval, self._drain_weather_events)
        self.after(self._data_poll_interval, self._drain_news_events)
        self.after(450, self._load_news_feeds)
        if not self._pi_lite:
            self.after(self._ticker_interval, self._tick_weather_ticker)
            self.after(self._ticker_interval, self._tick_news_ticker)
            self.after(self._meter_interval, self._animate_audio_meter)

    def _position_tuner(self, _event=None):
        """Center the tuner card in its lane and redraw its vertical light rails."""
        if not hasattr(self, "_tuner_window"):
            return
        canvas = self.tuner_stage
        card = self.tuner_card
        card.update_idletasks()
        card_height = card.winfo_reqheight()
        card_width = card.winfo_reqwidth()
        stage_height = max(canvas.winfo_height(), card_height + 20)
        top = max(10, (stage_height - card_height) // 2)
        canvas.coords(self._tuner_window, canvas.winfo_width() / 2, top)
        canvas.itemconfigure(self._tuner_window, width=min(card_width, 148))
        self._schedule_panel_glows()

    def _schedule_panel_glows(self, _event=None):
        if self._panel_glow_job is not None:
            try:
                self.after_cancel(self._panel_glow_job)
            except tk.TclError:
                pass
        self._panel_glow_job = self.after(100, self._draw_panel_glows)

    def _draw_panel_glows(self):
        self._panel_glow_job = None
        if not hasattr(self, "panel_glow_canvas") or self._radio_suspended:
            return
        canvas = self.panel_glow_canvas
        width, height = canvas.winfo_width(), canvas.winfo_height()
        if width < 10 or height < 10:
            return
        scale = 0.5
        glow = Image.new("RGBA", (max(1, round(width * scale)),
                                  max(1, round(height * scale))), (0, 0, 0, 0))
        draw = ImageDraw.Draw(glow, "RGBA")
        blocks = []
        for widget, tint, top_blue_glow in (
                (getattr(self, "map_panel", None), (80, 170, 255, 160), True),
                (getattr(self, "tuner_stage", None), (145, 255, 180, 105), False),
                (getattr(self, "station_panel", None), (80, 170, 255, 160), True)):
            if widget is None:
                continue
            blocks.append((widget.winfo_x(), widget.winfo_y(),
                           widget.winfo_x() + widget.winfo_width(),
                           widget.winfo_y() + widget.winfo_height(), tint))
        for x1, y1, x2, y2, tint in blocks:
            x1, y1, x2, y2 = (value * scale for value in (x1, y1, x2, y2))
            center_x = (x1 + x2) / 2
            radius_x = max(24, (x2 - x1) * 0.48)
            glow_y = y2 + 6
            draw.ellipse((center_x - radius_x, glow_y - 22,
                          center_x + radius_x, glow_y + 26),
                         fill=tint)
            if top_blue_glow:
                top_y = y1 - 6
                draw.ellipse((center_x - radius_x, top_y - 26,
                              center_x + radius_x, top_y + 22),
                             fill=tint)
        soft = glow.filter(ImageFilter.GaussianBlur(18))
        wide = glow.filter(ImageFilter.GaussianBlur(34))
        glow = Image.alpha_composite(wide, soft).resize(
            (width, height), Image.Resampling.LANCZOS)
        self._panel_glow_photo = ImageTk.PhotoImage(glow)
        if self._panel_glow_item is None:
            self._panel_glow_item = canvas.create_image(
                0, 0, image=self._panel_glow_photo, anchor="nw")
        else:
            canvas.itemconfigure(self._panel_glow_item, image=self._panel_glow_photo)
        canvas.tag_lower(self._panel_glow_item)

        # A separate diffuse mint halo sits behind the dark tuner card only.
        tuner_canvas = self.tuner_stage
        tuner_bbox = tuner_canvas.bbox(self._tuner_window)
        if tuner_bbox:
            tuner_width = max(1, round(tuner_canvas.winfo_width() * scale))
            tuner_height = max(1, round(tuner_canvas.winfo_height() * scale))
            tuner_glow = Image.new("RGBA", (tuner_width, tuner_height), (0, 0, 0, 0))
            tuner_draw = ImageDraw.Draw(tuner_glow, "RGBA")
            x1, y1, x2, y2 = (value * scale for value in tuner_bbox)
            tuner_draw.rounded_rectangle(
                (x1 - 10, y1 - 12, x2 + 10, y2 + 12), radius=24,
                fill=(145, 255, 180, 82))
            tuner_draw.rounded_rectangle(
                (x1 - 24, y1 - 28, x2 + 24, y2 + 28), radius=34,
                fill=(145, 255, 180, 45))
            tuner_glow = tuner_glow.filter(ImageFilter.GaussianBlur(20)).resize(
                (tuner_canvas.winfo_width(), tuner_canvas.winfo_height()),
                Image.Resampling.LANCZOS)
            self._tuner_static_glow_photo = ImageTk.PhotoImage(tuner_glow)
            if self._tuner_static_glow_item is None:
                self._tuner_static_glow_item = tuner_canvas.create_image(
                    0, 0, image=self._tuner_static_glow_photo, anchor="nw")
            else:
                tuner_canvas.itemconfigure(
                    self._tuner_static_glow_item, image=self._tuner_static_glow_photo)
            tuner_canvas.tag_lower(self._tuner_static_glow_item, self._tuner_window)


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

    def _refresh_favorite_tuner(self):
        if not hasattr(self, "favorite_tuner_scale"):
            return
        favorites = list(self.favorites.values())
        count = len(favorites)
        if count:
            selected = self.selected_station() if hasattr(self, "_row_stations") else None
            reference = selected or self.current
            current_id = station_id(reference) if reference else None
            favorite_ids = [station_id(station) for station in favorites]
            if current_id in favorite_ids:
                self.favorite_tuner_index = favorite_ids.index(current_id)
            self.favorite_tuner_index = min(max(0, self.favorite_tuner_index), count - 1)
            station = favorites[self.favorite_tuner_index]
            self.favorite_tuner_scale.configure(from_=1, to=count, state="normal")
            self.favorite_tuner_var.set(self.favorite_tuner_index + 1)
            self.favorite_tuner_station.configure(text=station.get("name", "Radio station"))
            self.favorite_tuner_position.configure(
                text=f"{self.favorite_tuner_index + 1:02d} / {count:02d}")
        else:
            self.favorite_tuner_index = 0
            self.favorite_tuner_scale.configure(from_=1, to=1, state="disabled")
            self.favorite_tuner_var.set(1)
            self.favorite_tuner_station.configure(text="No saved favourites")
            self.favorite_tuner_position.configure(text="0 / 0")
        self._draw_favorite_tuner_dial(count)

    def _draw_favorite_tuner_dial(self, count):
        canvas = self.favorite_tuner_canvas
        canvas.delete("all")
        width, center_y = 126, 25
        canvas.create_line(8, center_y, width - 8, center_y, fill="#536873", width=2)
        tick_count = min(max(count, 2), 15)
        for tick in range(tick_count):
            fraction = tick / max(1, tick_count - 1)
            x = 9 + fraction * (width - 18)
            long_tick = tick % 3 == 0
            canvas.create_line(x, center_y - (10 if long_tick else 6), x,
                               center_y + (10 if long_tick else 6),
                               fill="#8da2a8" if long_tick else "#536873", width=1)
        if count:
            fraction = self.favorite_tuner_index / max(1, count - 1)
            x = 9 + fraction * (width - 18)
            canvas.create_polygon(x - 5, 4, x + 5, 4, x, 12,
                                  fill="#f2c66d", outline="")
            canvas.create_line(x, 11, x, 39, fill="#f2c66d", width=2)
        canvas.create_oval(3, center_y - 2, 7, center_y + 2, fill="#d66a68", outline="")
        canvas.create_oval(width - 7, center_y - 2, width - 3, center_y + 2,
                           fill="#d66a68", outline="")

    def _preview_favorite_tuner(self, value):
        favorites = list(self.favorites.values())
        if not favorites:
            return
        index = min(len(favorites) - 1, max(0, int(float(value)) - 1))
        self.favorite_tuner_index = index
        station = favorites[index]
        self.favorite_tuner_station.configure(text=station.get("name", "Radio station"))
        self.favorite_tuner_position.configure(text=f"{index + 1:02d} / {len(favorites):02d}")
        self._draw_favorite_tuner_dial(len(favorites))

    def _tune_favorite_tuner(self, _event=None):
        favorites = list(self.favorites.values())
        if not favorites:
            self.set_status("Save stations as favourites to use the tuner")
            return "break"
        index = min(len(favorites) - 1, max(0, int(self.favorite_tuner_var.get()) - 1))
        self.favorite_tuner_index = index
        station = favorites[index]
        station_key = station_id(station)
        if station_key not in self._row_stations:
            self.only_favorites = True
            self.stations = favorites
            self.render()
        self._play_radio_station(station)
        self.set_status(f"Favourite {index + 1} of {len(favorites)} · {station.get('name', 'Radio')}")
        self._refresh_favorite_tuner()
        return "break"

    def _step_favorite_tuner(self, direction):
        favorites = list(self.favorites.values())
        if not favorites:
            self.set_status("Save stations as favourites to use the tuner")
            return
        favorite_ids = [station_id(station) for station in favorites]
        current_id = station_id(self.current) if self.current else None
        if current_id in favorite_ids:
            index = (favorite_ids.index(current_id) + direction) % len(favorites)
        else:
            index = 0 if direction > 0 else len(favorites) - 1
        self.favorite_tuner_index = index
        self.favorite_tuner_var.set(index + 1)
        self._tune_favorite_tuner()

    def toggle_favorite(self):
        super().toggle_favorite()
        self._refresh_favorite_tuner()

    def _build_ui(self):
        header = tk.Frame(self, bg=self.BG, height=42)
        header.pack(fill="x", padx=22, pady=0)
        header.pack_propagate(False)
        tk.Label(header, text="WORLD RADIO" if self._pi_lite else "◉  WORLD RADIO", bg=self.BG, fg=self.TEXT,
                 font=("DejaVu Sans", 16 if self._pi_lite else 21, "bold")).pack(side="left")
        tk.Label(header, text="CHOOSE A COUNTRY OR BROWSE WORLDWIDE" if self._pi_lite else "MAP EDITION  ·  CLICK A COUNTRY TO BROWSE", bg=self.BG,
                 fg=self.MUTED, font=("Segoe UI", 11, "bold")).pack(side="right")
        self.clock_label = tk.Label(header, text="LOCAL  --:--", bg="#17232d", fg="#e6c77a",
                                    font=("Consolas", 14, "bold"))
        self.clock_label.pack(side="right", padx=18, ipadx=10, ipady=5)
        self.station_header_title = tk.Label(
            self, text="Choose a station", bg=self.BG, fg="#f2c66d",
            font=("Segoe UI", 36, "bold"), anchor="center", justify="center")
        self.station_header_title.pack(fill="x", padx=20, pady=(0, 2), ipady=0)

        controls = tk.Frame(self, bg=self.PANEL, padx=12, pady=10)
        controls.pack(fill="x", padx=20)
        source_box = tk.Frame(controls, bg=self.PANEL)
        source_box.pack(side="right", padx=(8, 0))
        tk.Label(source_box, text="SOURCE", bg=self.PANEL, fg=self.MUTED,
                 font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 6))
        self.source_var = tk.StringVar(value=RADIO_SOURCES[0])
        self.source_picker = ttk.Combobox(source_box, textvariable=self.source_var,
            values=RADIO_SOURCES, state="readonly", width=20)
        self.source_picker.pack(side="left")
        self.source_picker.bind("<<ComboboxSelected>>", self._source_changed)
        self.search = tk.StringVar()
        entry = tk.Entry(controls, textvariable=self.search, bg=self.PANEL2, fg=self.TEXT,
                         insertbackground=self.TEXT, relief="flat", font=("Segoe UI", 12))
        entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 7))
        entry.insert(0, "Search all stations…")
        entry.bind("<FocusIn>", lambda _e: self._clear_placeholder(entry))
        entry.bind("<Return>", lambda _e: self.search_directory())
        self._button(controls, "Search", self.search_directory, primary=True).pack(side="left", padx=3)
        self._button(controls, "Popular worldwide", self.load_directory).pack(side="left", padx=3)
        self._button(controls, "♥ Favorites", self.show_favorites).pack(side="left", padx=3)

        content = tk.Frame(self, bg=self.BG)
        content.pack(fill="both", expand=True, padx=20, pady=(12, 10))
        self.panel_glow_canvas = tk.Canvas(content, bg=self.BG,
                                           highlightthickness=0, bd=0)
        self.panel_glow_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        left = tk.Frame(content, bg=self.PANEL, padx=12, pady=10)
        self.map_panel = left
        left.pack(side="left", fill="both", expand=True, padx=(0, 8), pady=(18, 18))
        top = tk.Frame(left, bg=self.PANEL)
        top.pack(fill="x", pady=(0, 7))
        self.map_caption = tk.Label(top, text="COUNTRY MAP" if self._pi_lite else "WORLD MAP  ·  STATION ORIGIN",
                                    bg=self.PANEL, fg=self.TEXT, font=("Segoe UI", 12, "bold"),
                                    width=25, anchor="w")
        self.map_caption.pack(side="left")
        self.country_choice = tk.StringVar(value="Choose a country…")
        self.country_picker = ttk.Combobox(top, textvariable=self.country_choice, state="readonly", width=25)
        self.country_picker.pack(side="right", padx=(8, 0))
        self.country_picker.bind("<<ComboboxSelected>>", self._country_picker_selected)
        self._button(top, "Clear", self.clear_map_selection).pack(side="right")
        if self._pi_lite:
            self.map_help_label = tk.Label(
                left, text="Choose a country to list its stations", bg=self.PANEL,
                fg=self.MUTED, font=("DejaVu Sans", 14), anchor="center")
            self.map_help_label.pack(fill="both", expand=True, padx=20, pady=20)
        else:
            self.map_canvas = tk.Canvas(left, bg="#0e1822", highlightthickness=0, cursor="hand2")
            self.map_canvas.pack(fill="both", expand=True)
            self._map_draw_size = None
            self._map_redraw_job = None
            self.map_canvas.bind("<Configure>", self._map_canvas_configured)
        self._load_map_data()

        # Keep the tuner centered between the map and station panels.
        self.tuner_stage = tk.Canvas(content, bg=self.BG, width=168,
                                     highlightthickness=0, bd=0)
        self.tuner_stage.pack(side="left", fill="y", padx=(0, 8), pady=(18, 18))
        tuner = tk.Frame(self.tuner_stage, bg="#17232d", padx=9, pady=12, width=148,
                         highlightthickness=0)
        self.tuner_card = tuner
        tuner.pack_propagate(True)
        self._tuner_window = self.tuner_stage.create_window(
            84, 0, window=tuner, anchor="n", width=148)
        self.tuner_stage.bind("<Configure>", self._position_tuner)
        tk.Label(tuner, text="FAVOURITE", bg="#17232d", fg="#9eb4bc",
                 font=("Segoe UI", 10, "bold")).pack(pady=(2, 0))
        tk.Label(tuner, text="TUNER", bg="#17232d", fg="#f2c66d",
                 font=("Segoe UI", 15, "bold")).pack(pady=(0, 8))
        self.favorite_tuner_canvas = tk.Canvas(
            tuner, width=126, height=44, bg="#0e1822", highlightthickness=0)
        self.favorite_tuner_canvas.pack(fill="x", pady=(0, 9))
        self.clock_overlay = tk.Frame(tuner, bg="#0e1720", padx=3, pady=3,
                                      height=138, highlightthickness=0)
        self.clock_overlay.pack(fill="x", pady=(0, 8))
        self.clock_overlay.pack_propagate(False)
        tk.Label(self.clock_overlay, text="LOCAL TIME", bg="#0e1720", fg="#8da8b5",
                 font=("Segoe UI", 10, "bold")).pack(pady=(0, 1))
        self.clock_canvas = tk.Canvas(self.clock_overlay, width=90, height=90,
                                      bg="#0e1720", highlightthickness=0)
        self.clock_canvas.pack()
        self.country_clock_label = tk.Label(
            self.clock_overlay, text="LOCAL TIME", bg="#0e1720", fg="#f2c66d",
            font=("Segoe UI", 10, "bold"), wraplength=120, height=2, justify="center")
        self.country_clock_label.pack(fill="x", pady=(0, 1))
        self.favorite_tuner_station = tk.Label(
            tuner, text="No saved favourites", bg="#17232d", fg=self.TEXT,
            font=("Segoe UI", 11, "bold"), wraplength=126, justify="center", height=3)
        self.favorite_tuner_station.pack(fill="x", pady=(0, 5))
        self.favorite_tuner_position = tk.Label(
            tuner, text="0 / 0", bg="#17232d", fg="#75d6c1",
            font=("Consolas", 12, "bold"))
        self.favorite_tuner_position.pack(pady=(0, 3))
        self.favorite_tuner_var = tk.IntVar(value=1)
        self.favorite_tuner_scale = tk.Scale(
            tuner, from_=1, to=1, orient="horizontal", variable=self.favorite_tuner_var,
            showvalue=False, resolution=1, length=126, width=6, sliderlength=17,
            bd=0, highlightthickness=0, relief="flat", bg="#17232d", fg=self.TEXT,
            troughcolor="#40535d", activebackground="#f2c66d",
            command=self._preview_favorite_tuner)
        self.favorite_tuner_scale.pack(fill="x", pady=(0, 9))
        self.favorite_tuner_scale.bind("<ButtonRelease-1>", self._tune_favorite_tuner)
        self.favorite_tuner_scale.bind("<KeyRelease>", self._tune_favorite_tuner)
        tune_buttons = tk.Frame(tuner, bg="#17232d")
        tune_buttons.pack(side="bottom", fill="x", pady=(8, 2))
        self._button(tune_buttons, "◀", lambda: self._step_favorite_tuner(-1)).pack(
            side="left", fill="x", expand=True, padx=(0, 3))
        self._button(tune_buttons, "▶", lambda: self._step_favorite_tuner(1),
                     primary=True).pack(side="left", fill="x", expand=True, padx=(3, 0))
        if not self._pi_lite:
            self.analog_audio_meter = tk.Canvas(
                tuner, width=126, height=100, bg="#17232d", highlightthickness=0)
            self.analog_audio_meter.pack(side="bottom", fill="x", pady=(4, 8))

        station_bg = "#101821"
        station_header_bg = "#1a2732"
        right = tk.Frame(content, bg=station_bg, padx=10, pady=10, width=470,
                         bd=0, relief="flat", highlightthickness=0)
        self.station_panel = right
        right.pack(side="right", fill="both", expand=True, padx=(8, 0), pady=(18, 18))
        right.pack_propagate(False)
        row = tk.Frame(right, bg=station_bg, bd=0, highlightthickness=0)
        row.pack(fill="x", pady=(0, 8))
        tk.Label(row, text="STATIONS", bg=station_bg, fg=self.TEXT,
                 font=("Segoe UI", 12, "bold")).pack(side="left")
        self.count_label = tk.Label(row, text="Connecting…", bg=station_bg, fg=self.MUTED,
                                    font=("Segoe UI", 10))
        self.count_label.pack(side="right")
        self.weather_card = tk.Frame(right, bg="#1a2b32", padx=11, pady=8,
                                     bd=0, relief="flat", highlightthickness=0)
        self.weather_card.pack(fill="x", pady=(0, 8))
        self.weather_icon = tk.Label(self.weather_card, text="" if self._pi_lite else "◌", bg="#1a2b32", fg="#70d9ce",
                                     font=("DejaVu Sans", 13 if self._pi_lite else 23, "bold"), width=1 if self._pi_lite else 2)
        if not self._pi_lite:
            self.weather_icon.pack(side="left", padx=(0, 8))
        weather_text = tk.Frame(self.weather_card, bg="#1a2b32")
        weather_text.pack(side="left", fill="x", expand=True)
        self.weather_title = tk.Label(weather_text, text="COUNTRY WEATHER", bg="#1a2b32",
                                      fg="#a8ded6", font=("Segoe UI", 10, "bold"), anchor="w")
        self.weather_title.pack(anchor="w")
        self.weather_detail = tk.Label(weather_text, text="Select a country for current conditions",
                                       bg="#1a2b32", fg=self.TEXT, font=("Segoe UI", 12), anchor="w", justify="left")
        self.weather_detail.pack(anchor="w", pady=(2, 0))
        self.weather_source = tk.Label(weather_text, text="Open-Meteo · representative location",
                                       bg="#1a2b32", fg=self.MUTED, font=("Segoe UI", 10), anchor="w")
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
                         font=("Segoe UI", 10, "bold")).pack(anchor="w")
                value = tk.Label(tile, text="—", bg="#223b46", fg=color,
                                 font=("Segoe UI", 12, "bold"))
                value.pack(anchor="w")
                self.weather_metrics[key] = value
        if not self._pi_lite:
            self.weather_ticker = tk.Canvas(self.weather_card, height=24, bg="#10202a",
                                            highlightthickness=0)
            self.weather_ticker.pack(fill="x", pady=(0, 2))
            self.weather_ticker.bind("<Configure>", self._reset_weather_ticker)
            self.weather_ticker_item = self.weather_ticker.create_text(
                8, 12, text=self.weather_ticker_message, anchor="w",
                fill="#a9e6dd", font=("Segoe UI", 12, "bold"))
        columns = ("name", "genre", "bitrate")
        station_style = ttk.Style(self)
        station_style.configure(
            "RadioStations.Treeview", background=station_bg, foreground=self.TEXT,
            fieldbackground=station_bg, font=("Segoe UI", 18), rowheight=48,
            borderwidth=0, relief="flat", bordercolor=station_bg,
            lightcolor=station_bg, darkcolor=station_bg)
        station_style.configure(
            "RadioStations.Treeview.Heading", background=station_header_bg,
            foreground=self.MUTED, font=("Segoe UI", 12, "bold"),
            relief="flat", borderwidth=0)
        station_style.map("RadioStations.Treeview",
                          background=[("selected", "#28543f")],
                          foreground=[("selected", "white")])
        station_style.layout("RadioStations.Treeview", [
            ("Treeview.treearea", {"sticky": "nswe"}),
        ])
        self.table = ttk.Treeview(
            right, columns=columns, show="headings", selectmode="browse",
            style="RadioStations.Treeview", takefocus=True)
        for key, title in (("name", "STATION"), ("genre", "GENRE"), ("bitrate", "KBPS")):
            self.table.heading(key, text=title)
        self.table.column("name", width=260, minwidth=170)
        self.table.column("genre", width=105, minwidth=70)
        self.table.column("bitrate", width=55, minwidth=45, anchor="center")
        scroll = ttk.Scrollbar(right, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scroll.set)
        self.table.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.table.bind("<<TreeviewSelect>>", self._station_list_selected)
        self.table.bind("<Double-1>", lambda _e: self.play_selected())
        self.table.bind("<Return>", lambda _e: self.play_selected())
        self.table.bind("<space>", lambda _e: self.play_selected())
        self._refresh_favorite_tuner()
        self.after(80, self._position_tuner)
        content.bind("<Configure>", self._schedule_panel_glows)
        self.after(140, self._draw_panel_glows)

        news_bar = tk.Frame(self, bg="#131e29", padx=10, pady=7,
                            highlightthickness=0)
        news_tabs = tk.Frame(news_bar, bg="#131e29")
        news_tabs.pack(side="left", padx=(0, 10))
        tk.Label(news_tabs, text="NEWS", bg="#131e29", fg="#f2bd55",
                 font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 6))
        self.news_buttons = {}
        for section in NEWS_SECTIONS:
            button = tk.Button(news_tabs, text=section, command=lambda name=section: self._select_news_section(name),
                               bg="#293a49", fg=self.TEXT, activebackground="#365166",
                               activeforeground=self.TEXT, relief="flat", bd=0, cursor="hand2",
                               padx=9, pady=4, font=("Segoe UI", 10, "bold"))
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
                                        font=("DejaVu Sans", 12, "bold"), wraplength=800)
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
        now_heading = tk.Frame(now, bg=self.PANEL)
        now_heading.pack(fill="x")
        self.now_title = tk.Label(now_heading, text="Choose a station to start listening", bg=self.PANEL,
                                  fg=self.TEXT, font=("Segoe UI", 22, "bold"), anchor="w")
        self.now_title.pack(side="left", anchor="w")
        if not self._pi_lite:
            self.audio_meter = tk.Canvas(now_heading, width=150, height=42, bg=self.PANEL,
                                         highlightthickness=0)
            self.audio_meter.pack(side="left", padx=(16, 12))
            self.audio_meter.create_text(2, 2, text="AUDIO", anchor="nw", fill=self.MUTED,
                                         font=("Segoe UI", 11, "bold"), tags="meter-label")
        self.status = tk.Label(now, text="Directory powered by Radio Browser", bg=self.PANEL,
                               fg=self.MUTED, font=("Segoe UI", 12), anchor="w")
        self.status.pack(anchor="w", pady=(2, 0))
        actions = tk.Frame(foot, bg=self.PANEL)
        actions.pack(side="left", padx=10)
        self._button(actions, "▶ Play", self.play_selected, primary=True).pack(side="left", padx=2)
        self._button(actions, "Ⅱ", self.pause).pack(side="left", padx=2)
        self._button(actions, "■", self.stop).pack(side="left", padx=2)
        self._button(actions, "♥", self.toggle_favorite).pack(side="left", padx=2)
        vol = tk.Frame(foot, bg=self.PANEL)
        vol.configure(width=300, height=34)
        vol.pack(side="right", padx=(8, 0))
        vol.pack_propagate(False)
        self.volume = tk.IntVar(value=75)
        tk.Label(vol, text="VOL", bg=self.PANEL, fg=self.MUTED,
                 font=("Segoe UI", 12, "bold")).pack(side="left", padx=(2, 7))
        self.volume_scale = tk.Scale(vol, from_=0, to=100, orient="horizontal",
            variable=self.volume, showvalue=False, resolution=1, length=205, width=5,
            sliderlength=15, bd=0, highlightthickness=0, relief="flat",
            bg=self.PANEL, fg=self.TEXT, troughcolor="#354653",
            activebackground="#79e1c2", command=self.set_volume)
        self.volume_scale.pack(side="left", fill="x", expand=True, padx=(0, 7))
        self.volume_bubble = tk.Label(vol, text="75%", width=4, bg="#293a49", fg=self.TEXT,
            font=("Segoe UI", 12, "bold"), padx=4, pady=3)
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
        # Use one geographic scale on both axes. The projection is stable and
        # the continents cannot stretch or jump when the canvas is resized.
        scale = min((width - pad * 2) / 360.0, (height - pad * 2) / 164.0)
        map_w, map_h = 360.0 * scale, 164.0 * scale
        offset_x = (width - map_w) / 2
        offset_y = (height - map_h) / 2
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
                    x = offset_x + (lon + 180) * scale
                    y = offset_y + (82 - lat) * scale
                    points.extend((x, y))
                    last_lon = lon
                if len(points) >= 6:
                    self._draw_country_piece(points, name, code, fill, outline)
        # The bundled low-detail geography omits Singapore as a polygon. Keep
        # a small, unlabeled marker at its true position so selection highlights
        # remain visible without shifting or rebuilding the rest of the map.
        singapore = self.country_by_code.get("SG")
        singapore_props = singapore.get("properties", {}) if singapore else {}
        try:
            sg_lon = float(singapore_props.get("LABEL_X", 103.8198))
            sg_lat = float(singapore_props.get("LABEL_Y", 1.3521))
            sg_x = offset_x + (sg_lon + 180) * scale
            sg_y = offset_y + (82 - sg_lat) * scale
            sg_selected = str(self.map_country_code or "").upper() == "SG"
            marker = self.map_canvas.create_oval(
                sg_x - 4, sg_y - 4, sg_x + 4, sg_y + 4,
                fill="#35c982" if sg_selected else "#547184",
                outline="#b9ffd9" if sg_selected else "#78909d",
                width=1, tags=("mapshape", "country:SG"))
            self.map_canvas.tag_bind(marker, "<Button-1>",
                lambda _event: self.select_map_country("Singapore", "SG"))
            self.map_canvas.tag_bind(marker, "<Enter>",
                lambda _event: self.map_canvas.configure(cursor="hand2"))
        except (TypeError, ValueError):
            pass
        self._map_drawn_selected_code = str(self.map_country_code or "").upper()

    def _map_canvas_configured(self, event):
        """Coalesce layout notifications; station selection never rebuilds the map."""
        size = (event.width, event.height)
        if size == self._map_draw_size or min(size) < 10:
            return
        if self._map_redraw_job is not None:
            try:
                self.after_cancel(self._map_redraw_job)
            except tk.TclError:
                pass
        self._map_redraw_job = self.after(80, self._redraw_map_at_current_size)

    def _redraw_map_at_current_size(self):
        self._map_redraw_job = None
        if not hasattr(self, "map_canvas") or not self.map_canvas.winfo_exists():
            return
        size = (self.map_canvas.winfo_width(), self.map_canvas.winfo_height())
        if size == self._map_draw_size or min(size) < 10:
            return
        self._map_draw_size = size
        self.draw_map()

    def _update_map_highlight(self):
        """Recolor existing country polygons without rebuilding/resizing the map."""
        if not hasattr(self, "map_canvas"):
            return
        selected_code = str(self.map_country_code or "").upper()
        previous_code = self._map_drawn_selected_code
        if previous_code == selected_code:
            return
        for code in {previous_code, selected_code} - {None, ""}:
            selected = code == selected_code
            for item in self.map_canvas.find_withtag(f"country:{code}"):
                self.map_canvas.itemconfigure(
                    item, fill="#35c982" if selected else "#263e50",
                    outline="#b9ffd9" if selected else "#547184")
        self._map_drawn_selected_code = selected_code
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
        self._apply_map_country(name, code)
        self.search_directory()

    def _apply_map_country(self, name, code):
        self.map_country_name, self.map_country_code = name, code
        self.country_choice.set(name)
        self._load_weather(name, code)
        self.country_time_name = name
        self.country_timezone = None
        self.country_utc_offset_seconds = None
        self.country_timezone_status = "loading"
        self.country_clock_label.configure(text=f"{name} · loading time zone…")
        self._update_map_highlight()

    def _country_for_station(self, station):
        country = (station.get("country") or "").strip()
        code = (station.get("countrycode") or station.get("country_code") or "").strip().upper()
        code_aliases = {"UK": "GB", "USA": "US", "U.S.": "US", "SGP": "SG", "IND": "IN"}
        code = code_aliases.get(code, code)
        if code:
            name = next((name for name, mapped_code in self.country_by_name.items()
                         if mapped_code.upper() == code), None)
            feature = self.country_by_code.get(code)
            if not name and feature:
                props = feature.get("properties", {})
                name = props.get("ADMIN") or props.get("NAME")
            if name:
                return name, code
        if not country:
            return None, None
        folded = country.casefold()
        name = next((name for name in self.country_by_name if name.casefold() == folded), None)
        if name:
            return name, self.country_by_name[name]
        aliases = {
            "united kingdom": ("United Kingdom of Great Britain and Northern Ireland", "GB"),
            "great britain": ("United Kingdom", "GB"),
            "uk": ("United Kingdom", "GB"),
            "united states": ("United States of America", "US"),
            "united states of america": ("United States", "US"),
            "usa": ("United States", "US"),
            "south korea": ("Republic of Korea", "KR"),
            "russia": ("Russian Federation", "RU"),
            "vietnam": ("Viet Nam", "VN"),
            "tanzania": ("United Republic of Tanzania", "TZ"),
            "bolivia": ("Plurinational State of Bolivia", "BO"),
        }
        alias_name, alias_code = aliases.get(folded, (country, None))
        name = next((name for name in self.country_by_name
                     if name.casefold() == alias_name.casefold()), None)
        if name:
            return name, self.country_by_name[name]
        if alias_code:
            name = next((name for name, mapped_code in self.country_by_name.items()
                         if mapped_code.upper() == alias_code), None)
            if name:
                return name, self.country_by_name[name]
        return None, None

    def _station_list_selected(self, _event=None):
        station = self.selected_station()
        if not station:
            return
        name = (station.get("name") or "Internet radio").strip()
        country = (station.get("country") or "Online").strip()
        title = f"{name}  ·  {country}"
        self.now_title.configure(text=title)
        self.station_header_title.configure(text=title)
        self._sync_favorite_tuner_to_station(station)
        map_name, map_code = self._country_for_station(station)
        if map_name and map_code and map_code != self.map_country_code:
            self._apply_map_country(map_name, map_code)

    def _sync_favorite_tuner_to_station(self, station):
        favorite_ids = [station_id(item) for item in self.favorites.values()]
        station_key = station_id(station)
        if station_key in favorite_ids:
            self.favorite_tuner_index = favorite_ids.index(station_key)
            self.favorite_tuner_var.set(self.favorite_tuner_index + 1)
            self.favorite_tuner_position.configure(
                text=f"{self.favorite_tuner_index + 1:02d} / {len(favorite_ids):02d}")
            self.favorite_tuner_station.configure(text=station.get("name", "Radio station"))
            self._draw_favorite_tuner_dial(len(favorite_ids))
        else:
            self.favorite_tuner_station.configure(text=station.get("name", "Radio station"))
            self.favorite_tuner_position.configure(text="NOT IN FAVOURITES")
            self._draw_favorite_tuner_dial(0)

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
        width = max(90, canvas.winfo_width())
        height = max(90, canvas.winfo_height())
        cx, cy = width / 2, height / 2
        radius = min(width, height) / 2 - 3
        # Numerals replace the old outlined dial and dense tick marks.
        for hour_number in range(1, 13):
            angle = math.radians(hour_number * 30 - 90)
            number_radius = radius * 0.78
            x = cx + number_radius * math.cos(angle)
            y = cy + number_radius * math.sin(angle)
            color = "#f2c66d" if hour_number == 12 else "#c3d0d5"
            canvas.create_text(x, y, text=str(hour_number), fill=color,
                               font=("Segoe UI", 10, "bold"), tags="clock")
        second = now.second
        minute = now.minute + second / 60
        hour = (now.hour % 12) + minute / 60
        for value, degrees, length, color, weight in (
                (hour, 30, radius * 0.40, "#f2c66d", 4),
                (minute, 6, radius * 0.61, "#eaf2f3", 3),
                (second, 6, radius * 0.70, "#69cfc0", 1)):
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
        self.country_time_name = None
        self.country_timezone = None
        self.country_utc_offset_seconds = None
        self.country_timezone_status = "local"
        self.country_clock_label.configure(text="LOCAL TIME")
        self.country_choice.set("Choose a country…")
        self.map_caption.configure(text="COUNTRY MAP" if self._pi_lite else "WORLD MAP  ·  STATION ORIGIN")
        self.weather_title.configure(text="COUNTRY WEATHER")
        self.weather_icon.configure(text="◌")
        self.weather_detail.configure(text="Select a country for current conditions")
        self.weather_source.configure(text="Open-Meteo · representative location")
        self.weather_color = "#47c98b"
        for metric in self.weather_metrics.values():
            metric.configure(text="—")
        self.weather_ticker_message = "Select a country to see local weather and the next hours"
        self._reset_weather_ticker()
        self._update_map_highlight()
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
            self.country_time_name = None
            self.country_timezone = None
            self.country_utc_offset_seconds = None
            self.country_timezone_status = "local"
            self.country_clock_label.configure(text="LOCAL TIME")
            if hasattr(self, "country_choice"):
                self.country_choice.set("Choose a country…")
                self.map_caption.configure(text="COUNTRY MAP" if self._pi_lite else "WORLD MAP  ·  STATION ORIGIN")
                self.weather_title.configure(text="COUNTRY WEATHER")
                self.weather_icon.configure(text="◌")
                self.weather_detail.configure(text="Select a country for current conditions")
                self.weather_source.configure(text="Open-Meteo · representative location")
                self.weather_color = "#47c98b"
                for metric in self.weather_metrics.values():
                    metric.configure(text="—")
                self.weather_ticker_message = "Select a country to see local weather and the next hours"
                self._reset_weather_ticker()
                self._update_map_highlight()
        source = self.source_var.get() if hasattr(self, "source_var") else RADIO_SOURCES[0]
        if source == "IPRD":
            self._load_iprd_catalog(all_countries=True)
            return
        if source == "Verified Radio":
            self._load_verified_stations(all_countries=True)
            return
        if source == "Akashvani":
            self._load_akashvani_stations(all_countries=True)
            return
        if source == "BBC":
            self._load_bbc_stations()
            return
        if source == "Mediacorp":
            self._load_mediacorp_stations()
            return
        if source == "SouthRadios":
            self._load_southradios_stations(all_countries=True)
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
        meter_levels = []
        for index in range(bars):
            wave = (math.sin(self.meter_phase + index * 0.73) +
                    0.45 * math.sin(self.meter_phase * 1.7 + index * 1.19))
            level = (0.12 + 0.78 * abs(wave)) if playing else 0.06
            meter_levels.append(level)
            bar_height = max(2, available * level)
            x1 = 4 + index * (bar_width + gap)
            canvas.create_rectangle(x1, baseline - bar_height, x1 + bar_width, baseline,
                                    fill=colors[min(len(colors) - 1,
                                                    int(level * len(colors)))],
                                    outline="", tags="meter-bar")
        channel_levels = tuple(
            sum(meter_levels[start:end]) / (end - start)
            for start, end in ((0, 5), (5, 10), (10, 16)))
        if hasattr(self, "analog_audio_meter"):
            self._draw_analog_audio_meter(playing)
        self.after(self._meter_interval, self._animate_audio_meter)

    def _draw_analog_audio_meter(self, playing):
        canvas = self.analog_audio_meter
        canvas.delete("all")
        width = max(120, canvas.winfo_width())
        height = max(88, canvas.winfo_height())
        cx, cy = width / 2, height - 13
        radius = min(width / 2 - 8, height - 29)
        canvas.create_text(cx, 8, text="SIGNAL", anchor="n", fill="#91a6ad",
                           font=("Segoe UI", 10, "bold"))

        def point(fraction, distance):
            angle = math.radians(210 + 120 * fraction)
            return cx + distance * math.cos(angle), cy + distance * math.sin(angle)

        for start, end, color in ((0.0, 0.62, "#55d6a0"),
                                  (0.62, 0.84, "#e5c65b"),
                                  (0.84, 1.0, "#e87561")):
            points = [point(start + (end - start) * step / 18, radius)
                      for step in range(19)]
            canvas.create_line(*[coordinate for xy in points for coordinate in xy],
                               fill=color, width=4, capstyle="round", tags="dial")

        for index in range(11):
            fraction = index / 10
            x1, y1 = point(fraction, radius - 1)
            x2, y2 = point(fraction, radius - (9 if index % 5 == 0 else 5))
            canvas.create_line(x1, y1, x2, y2, fill="#d2dfe2" if index % 5 == 0 else "#71858c",
                               width=1, tags="dial")
        for index, label in ((0, "0"), (5, "5"), (10, "10")):
            x, y = point(index / 10, radius - 17)
            canvas.create_text(x, y, text=label, fill="#d2dfe2",
                               font=("Segoe UI", 10, "bold"), tags="dial")

        wave = (math.sin(self.meter_phase * 1.3) + 0.45 * math.sin(self.meter_phase * 2.1))
        level = min(0.94, 0.12 + 0.78 * abs(wave)) if playing else 0.015
        nx, ny = point(level, radius - 11)
        canvas.create_line(cx, cy, nx, ny, fill="#f2c66d", width=2,
                           capstyle="round", tags="needle")
        canvas.create_oval(cx - 3, cy - 3, cx + 3, cy + 3,
                           fill="#f2c66d", outline="", tags="needle")

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
        if source == "Akashvani":
            self._load_akashvani_stations(all_countries=not bool(self.map_country_code))
            return
        if source == "BBC":
            self._load_bbc_stations()
            return
        if source == "Mediacorp":
            self._load_mediacorp_stations()
            return
        if source == "SouthRadios":
            self._load_southradios_stations(all_countries=not bool(self.map_country_code))
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

    def _load_akashvani_stations(self, all_countries=False):
        if self.akashvani_catalog is not None:
            self._show_external_stations(self.akashvani_catalog, "Akashvani", all_countries)
            return

        def fetch():
            payload = self._fetch_json(AKASHVANI_STATIONS_URL)
            rows = []
            for item in payload if isinstance(payload, list) else []:
                station = self._external_station(
                    "akashvani", item.get("epg_id") or item.get("stream_url"),
                    item.get("name"), "India", item.get("stream_url"),
                    ", ".join(value for value in
                              (item.get("state", ""), item.get("language", "")) if value),
                    "HLS")
                if station:
                    rows.append(station)
            return rows

        self.async_call(fetch, self._akashvani_loaded, "Loading Akashvani station streams…")

    def _akashvani_loaded(self, rows):
        self.akashvani_catalog = rows
        self._show_external_stations(rows, "Akashvani", all_countries=not bool(self.map_country_code))

    def _load_bbc_stations(self):
        if self.bbc_catalog is None:
            self.bbc_catalog = [
                station for name, key, stream, tags in BBC_STATIONS
                if (station := self._external_station(
                    "bbc", key, name, "United Kingdom", stream, tags, "HLS"))
            ]
        self._show_external_stations(self.bbc_catalog, "BBC", all_countries=True)
        self.set_status(f"BBC · {len(self.stations):,} live stations · international feeds")

    def _load_mediacorp_stations(self):
        if self.mediacorp_catalog is None:
            self.mediacorp_catalog = [
                station for name, stream_id, tags in MEDIACORP_STATIONS
                if (station := self._external_station(
                    "mediacorp", stream_id, name, "Singapore",
                    f"https://playerservices.streamtheworld.com/api/livestream-redirect/{stream_id}.aac",
                    tags, "AAC"))
            ]
        self._show_external_stations(self.mediacorp_catalog, "Mediacorp", all_countries=True)
        self.set_status(f"Mediacorp · {len(self.stations):,} live stations · Singapore")

    def _load_southradios_stations(self, all_countries=False):
        if self.southradios_catalog is not None:
            self._show_external_stations(self.southradios_catalog, "SouthRadios", all_countries)
            return

        def fetch_catalog():
            found = {}

            def lookup(name):
                try:
                    rows = api_get("/stations/search", {
                        "name": name, "limit": 400,
                        "order": "clickcount", "reverse": "true", "hidebroken": "true",
                    })
                    return name, rows if isinstance(rows, list) else []
                except Exception:
                    return name, []

            # Broad Tamil searches recover channels whose directory record uses
            # a SouthRadios-branded title instead of the short name on the site.
            queries = (*SOUTHRADIOS_STATION_NAMES, "SouthRadios", "Tamil")
            with ThreadPoolExecutor(max_workers=6) as pool:
                futures = [pool.submit(lookup, name) for name in queries]
                for future in as_completed(futures):
                    target, rows = future.result()
                    target_key = re.sub(r"[^a-z0-9]+", "", target.casefold())
                    for item in rows:
                        homepage = (item.get("homepage") or "").casefold()
                        station_name = (item.get("name") or "").strip()
                        station_key = re.sub(r"[^a-z0-9]+", "", station_name.casefold())
                        is_southradios = "southradios.com" in homepage
                        is_named_match = (target_key not in {"southradios", "tamil"}
                                          and (target_key in station_key or station_key in target_key))
                        if not is_southradios and not is_named_match:
                            continue
                        stream = item.get("url_resolved") or item.get("url")
                        station = self._external_station(
                            "southradios", item.get("stationuuid") or stream,
                            station_name or target, item.get("country") or "India",
                            stream, item.get("tags", ""), item.get("codec", ""),
                            item.get("bitrate", 0), item.get("clickcount", 0))
                        if station:
                            station["stationuuid"] = item.get("stationuuid") or station["stationuuid"]
                            found[station_id(station)] = station
            return sorted(found.values(), key=lambda row: row["name"].casefold())

        self.async_call(fetch_catalog, self._southradios_loaded,
                        "Finding SouthRadios live streams…")

    def _southradios_loaded(self, rows):
        # Retry on a later selection if the directory was temporarily empty.
        self.southradios_catalog = rows or None
        self._show_external_stations(rows, "SouthRadios", all_countries=not bool(self.map_country_code))
        if rows:
            self.set_status(f"SouthRadios · {len(rows):,} directory streams")
        else:
            self.set_status("No SouthRadios streams found in the directory right now. Try again later.")

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
        previous_selection = self.table.selection()
        previous_selected_id = previous_selection[0] if previous_selection else None
        for item in self.table.get_children():
            self.table.delete(item)
        for station in rows:
            name = (station.get("name") or "Untitled station").strip()
            if self.current and station_id(station) == station_id(self.current):
                name = "▶ " + name
            self.table.insert("", "end", iid=str(hash(station_id(station))), values=(
                name, (station.get("tags") or "—")[:25], station.get("bitrate", 0) or "—"))
        self._row_stations = {str(hash(station_id(station))): station for station in rows}
        selected_id = previous_selected_id if previous_selected_id in self._row_stations else None
        if selected_id is None and self.current:
            playing_id = str(hash(station_id(self.current)))
            if playing_id in self._row_stations:
                selected_id = playing_id
        if selected_id:
            self.table.selection_set(selected_id)
            self.table.see(selected_id)
        label = f"{len(rows):,} stations"
        if self.map_country_name and not self.only_favorites:
            label += f" · {self.map_country_name}"
        elif self.only_favorites:
            label += " · Favorites"
        self.count_label.configure(text=label)
        self._refresh_favorite_tuner()


if __name__ == "__main__":
    app = WorldRadioMap()
    app.root.mainloop()

