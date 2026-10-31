"""RSS newspaper and magazine reader panel for SURAK MEDIA CENTER."""
from __future__ import annotations

from html.parser import HTMLParser
from io import BytesIO
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from urllib.parse import urljoin
import urllib.request
import webbrowser
import xml.etree.ElementTree as ET

try:
    import fitz
except ImportError:
    fitz = None

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = ImageTk = None


FEED_PRESETS = {
    "BBC · India": "https://feeds.bbci.co.uk/news/world/asia/india/rss.xml",
    "BBC · World": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "BBC · Top Stories": "https://feeds.bbci.co.uk/news/rss.xml",
    "BBC · Technology": "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "NDTV · India": "https://feeds.feedburner.com/ndtvnews-india-news",
    "NDTV · Top Stories": "https://feeds.feedburner.com/ndtvnews-top-stories",
    "NDTV · World": "https://feeds.feedburner.com/ndtvnews-world-news",
    "The Hindu · India": "https://www.thehindu.com/news/national/feeder/default.rss",
    "The Hindu · Top Stories": "https://www.thehindu.com/feeder/default.rss",
    "Sikkim Express · Latest": "https://www.sikkimexpress.com/Feed/rss_feed/latest-news",
    "Dina Thanthi · Tamil": "https://www.dailythanthi.com/feed",
    "The Guardian · World": "https://www.theguardian.com/world/rss",
    "The Guardian · News": "https://www.theguardian.com/international/rss",
    "The Guardian · Technology": "https://www.theguardian.com/technology/rss",
    "The Guardian · Books": "https://www.theguardian.com/books/rss",
    "The Guardian · Culture": "https://www.theguardian.com/culture/rss",
}


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.images = []
        self.hidden_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            image_url = dict(attrs).get("src")
            if image_url:
                self.images.append(image_url)
        if tag in ("script", "style"):
            self.hidden_depth += 1
        elif tag in ("p", "br", "div", "li", "h1", "h2", "h3"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.hidden_depth:
            self.hidden_depth -= 1
        elif tag in ("p", "div", "li"):
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.hidden_depth:
            self.parts.append(data)


def _plain_text(value):
    parser = _TextExtractor()
    try:
        parser.feed(value or "")
    except Exception:
        pass
    return " ".join(" ".join(parser.parts).split())


def _image_from_html(value):
    parser = _TextExtractor()
    try:
        parser.feed(value or "")
    except Exception:
        pass
    return parser.images[0] if parser.images else ""


def _tag_name(element):
    return element.tag.rsplit("}", 1)[-1].lower()


def _parse_feed(data):
    root = ET.fromstring(data)
    articles = []
    for item in root.iter():
        if _tag_name(item) not in ("item", "entry"):
            continue
        fields = {}
        image_url = ""
        for child in item:
            key = _tag_name(child)
            candidate_image = child.attrib.get("url", "")
            is_picture = (key == "thumbnail" or child.attrib.get("medium", "").lower() == "image"
                          or child.attrib.get("type", "").lower().startswith("image/"))
            if is_picture and candidate_image and not image_url:
                image_url = candidate_image
            if key == "enclosure" and child.attrib.get("type", "").startswith("image/"):
                image_url = image_url or candidate_image
            if key == "link":
                rel = child.attrib.get("rel", "alternate").lower()
                value = ((child.attrib.get("href") or (child.text or "").strip())
                         if rel in ("alternate", "") else "")
            else:
                value = "".join(child.itertext()).strip()
            if key not in fields and value:
                fields[key] = value
            if key in ("content:encoded", "encoded", "content"):
                fields["body"] = value
        link = fields.get("link", "")
        if not link:
            for child in item:
                if (_tag_name(child) == "link" and child.attrib.get("href")
                        and child.attrib.get("rel", "alternate").lower() in ("alternate", "")):
                    link = child.attrib["href"]
                    break
        title = _plain_text(fields.get("title", "Untitled article"))
        summary = _plain_text(fields.get("body") or fields.get("description")
                              or fields.get("summary", ""))
        image_url = image_url or _image_from_html(
            fields.get("body") or fields.get("description") or fields.get("summary", "")
        )
        articles.append({
            "title": title or "Untitled article",
            "summary": summary,
            "link": link,
            "date": fields.get("pubdate") or fields.get("published")
                    or fields.get("updated", ""),
            "image": image_url,
        })
    return articles


class MagazineReader(tk.Frame):
    BG = "#0b1118"
    PANEL = "#141e28"
    PANEL2 = "#202d37"
    TEXT = "#eef5f4"
    MUTED = "#91a6ad"
    ACCENT = "#55d6b0"

    def __init__(self, master):
        super().__init__(master, bg=self.BG)
        self.events = queue.Queue()
        self.image_events = queue.Queue()
        self.image_cache = {}
        self.image_url_current = ""
        self.article_photo = None
        self.articles = []
        self.closed = False
        self._view_suspended = False
        self.source_var = tk.StringVar(value=next(iter(FEED_PRESETS)))
        self.url_var = tk.StringVar(value=FEED_PRESETS[self.source_var.get()])
        self._build_ui()
        self.load_feed()
        self.after(120, self._drain_events)

    def _build_ui(self):
        header = tk.Frame(self, bg=self.BG)
        header.pack(fill="x", padx=22, pady=(18, 10))
        tk.Label(header, text="▤  NEWS & MAGAZINES", bg=self.BG, fg=self.TEXT,
                 font=("Segoe UI", 21, "bold")).pack(side="left")
        tk.Label(header, text="HEADLINES · SUMMARIES · READ ONLINE", bg=self.BG,
                 fg=self.MUTED, font=("Segoe UI", 9, "bold")).pack(side="right", pady=8)

        toolbar = tk.Frame(self, bg=self.PANEL, padx=12, pady=10)
        toolbar.pack(fill="x", padx=22)
        tk.Label(toolbar, text="Edition", bg=self.PANEL, fg=self.MUTED,
                 font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 7))
        picker = ttk.Combobox(toolbar, textvariable=self.source_var,
                              values=list(FEED_PRESETS) + ["Custom RSS feed"],
                              state="readonly", width=26)
        picker.pack(side="left", padx=(0, 8), ipady=4)
        picker.bind("<<ComboboxSelected>>", self._choose_feed)
        self.url_entry = tk.Entry(toolbar, textvariable=self.url_var, bg=self.PANEL2,
                                  fg=self.TEXT, insertbackground=self.TEXT,
                                  relief="flat", font=("Segoe UI", 9))
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 8), ipady=8)
        self.url_entry.bind("<Return>", lambda _event: self.load_feed())
        tk.Button(toolbar, text="Refresh", command=self.load_feed, bg="#278656",
                  fg=self.TEXT, activebackground="#39a96c", activeforeground=self.TEXT,
                  relief="flat", bd=0, cursor="hand2", padx=14, pady=8,
                  font=("Segoe UI", 9, "bold")).pack(side="left")
        tk.Button(toolbar, text="Open PDF magazine", command=self.open_magazine,
                  bg="#202b38", fg=self.TEXT, activebackground="#2b3948",
                  activeforeground=self.TEXT, relief="flat", bd=0, cursor="hand2",
                  padx=12, pady=8, font=("Segoe UI", 9, "bold")).pack(side="left", padx=(8, 0))

        body = tk.PanedWindow(self, orient="horizontal", bg=self.BG, bd=0,
                              sashwidth=5, relief="flat")
        body.pack(fill="both", expand=True, padx=22, pady=12)
        left = tk.Frame(body, bg=self.PANEL, padx=10, pady=10, width=390)
        right = tk.Frame(body, bg=self.PANEL, padx=22, pady=18)
        body.add(left, minsize=280, width=390)
        body.add(right, minsize=430)

        self.status = tk.Label(left, text="Loading headlines…", bg=self.PANEL,
                               fg=self.MUTED, font=("Segoe UI", 9), anchor="w")
        self.status.pack(fill="x", pady=(0, 8))
        list_shell = tk.Frame(left, bg=self.PANEL)
        list_shell.pack(fill="both", expand=True)
        scrollbar = ttk.Scrollbar(list_shell, orient="vertical")
        self.article_list = tk.Listbox(list_shell, bg=self.PANEL, fg=self.TEXT,
                                       selectbackground="#28543f", selectforeground="white",
                                       activestyle="none", relief="flat", bd=0,
                                       font=("Segoe UI", 10), yscrollcommand=scrollbar.set)
        scrollbar.configure(command=self.article_list.yview)
        self.article_list.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.article_list.bind("<<ListboxSelect>>", self._show_selected)

        self.article_title = tk.Label(right, text="Choose an article", bg=self.PANEL,
                                      fg=self.TEXT, font=("Segoe UI", 19, "bold"),
                                      justify="left", anchor="nw", wraplength=670)
        self.article_title.pack(fill="x", anchor="w")
        self.article_date = tk.Label(right, text="", bg=self.PANEL, fg=self.ACCENT,
                                     font=("Segoe UI", 9, "bold"), anchor="w")
        self.article_date.pack(fill="x", pady=(10, 16))
        self.article_image_label = tk.Label(right, text="", bg="#0d141b", fg=self.MUTED,
                                            font=("Segoe UI", 9), height=9)
        self.article_image_label.pack(fill="x", pady=(0, 14))
        self.article_summary = tk.Text(right, wrap="word", bg=self.PANEL, fg=self.TEXT,
                                       insertbackground=self.TEXT, relief="flat", bd=0,
                                       font=("Segoe UI", 12), padx=0, pady=2,
                                       spacing1=2, spacing3=8)
        self.article_summary.pack(fill="both", expand=True)
        self.article_summary.configure(state="disabled")
        self.open_button = tk.Button(right, text="Open news website view  ↗",
                                     command=self._open_selected, state="disabled",
                                     bg="#202b38", fg=self.TEXT,
                                     activebackground="#2b3948", activeforeground=self.TEXT,
                                     relief="flat", bd=0, cursor="hand2", padx=14, pady=9,
                                     font=("Segoe UI", 9, "bold"))
        self.open_button.pack(anchor="w", pady=(14, 0))

    def _choose_feed(self, _event=None):
        address = FEED_PRESETS.get(self.source_var.get(), "")
        self.url_var.set(address)
        if address:
            self.load_feed()

    def load_feed(self):
        url = self.url_var.get().strip()
        if not url.lower().startswith(("http://", "https://")):
            self.status.configure(text="Enter an RSS feed URL")
            return
        self.status.configure(text="Loading headlines…")
        self.article_list.delete(0, "end")

        def fetch():
            try:
                request = urllib.request.Request(url, headers={
                    "User-Agent": "SurakMediaCenter/1.0 (RSS reader)",
                    "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml",
                })
                with urllib.request.urlopen(request, timeout=20) as response:
                    data = response.read(8_000_000)
                articles = _parse_feed(data)
                if not articles:
                    raise ValueError("No articles were found in this feed")
                self.events.put((url, articles, None))
            except Exception as exc:
                self.events.put((url, None, str(exc)))

        threading.Thread(target=fetch, daemon=True).start()

    def _drain_events(self):
        if self._view_suspended or self.closed:
            return
        if self.closed or not self.winfo_exists():
            return
        try:
            while True:
                url, articles, error = self.events.get_nowait()
                if url != self.url_var.get().strip():
                    continue
                if error:
                    self.status.configure(text="Could not load feed; check the address or internet connection")
                    self._set_summary(f"The feed could not be loaded.\n\n{error}")
                    continue
                self.articles = articles
                self.article_list.delete(0, "end")
                for article in articles:
                    self.article_list.insert("end", article["title"])
                self.status.configure(text=f"{len(articles)} headlines · {self.source_var.get()}")
                if articles:
                    self.article_list.selection_set(0)
                    self.article_list.event_generate("<<ListboxSelect>>")
        except queue.Empty:
            pass
        self._drain_image_events()
        self.after(160, self._drain_events)

    def suspend_view(self):
        self._view_suspended = True

    def resume_view(self):
        if self._view_suspended and not self.closed:
            self._view_suspended = False
            self.after(160, self._drain_events)

    def _show_selected(self, _event=None):
        selection = self.article_list.curselection()
        if not selection or selection[0] >= len(self.articles):
            return
        article = self.articles[selection[0]]
        self.article_title.configure(text=article["title"])
        self.article_date.configure(text=article["date"])
        self._set_summary(article["summary"] or "Open the original article to read the full story.")
        self.open_button.configure(state="normal" if article["link"] else "disabled")
        raw_image_url = article.get("image", "")
        self.image_url_current = urljoin(article.get("link", ""), raw_image_url) if raw_image_url else ""
        self.article_photo = None
        self.article_image_label.configure(image="", text="", height=9)
        if self.image_url_current:
            cached = self.image_cache.get(self.image_url_current)
            if cached:
                self._show_image(cached)
            elif Image is not None:
                self.article_image_label.configure(text="Loading image…")
                self._request_image(self.image_url_current)

    def _set_summary(self, text):
        self.article_summary.configure(state="normal")
        self.article_summary.delete("1.0", "end")
        self.article_summary.insert("1.0", text)
        self.article_summary.configure(state="disabled")

    def _open_selected(self):
        selection = self.article_list.curselection()
        if selection and selection[0] < len(self.articles):
            link = self.articles[selection[0]].get("link")
            if link:
                webbrowser.open(link)

    def _request_image(self, url):
        def fetch():
            try:
                request = urllib.request.Request(url, headers={
                    "User-Agent": "SurakMediaCenter/1.0 (news reader)",
                })
                with urllib.request.urlopen(request, timeout=12) as response:
                    data = response.read(4_000_000)
                    content_type = response.headers.get("Content-Type", "")
                if not content_type.lower().startswith("image/") and not url.lower().endswith(
                        (".jpg", ".jpeg", ".png", ".webp", ".gif")):
                    raise ValueError("Feed image URL did not return an image")
                self.image_events.put((url, data, None))
            except Exception as exc:
                self.image_events.put((url, None, str(exc)))
        threading.Thread(target=fetch, daemon=True).start()

    def _show_image(self, image):
        if Image is None or ImageTk is None:
            return
        image = image.copy()
        image.thumbnail((760, 220), Image.Resampling.LANCZOS)
        self.article_photo = ImageTk.PhotoImage(image)
        self.article_image_label.configure(image=self.article_photo, text="", height=0)

    def _drain_image_events(self):
        try:
            while True:
                url, data, _error = self.image_events.get_nowait()
                if not data or Image is None:
                    continue
                try:
                    image = Image.open(BytesIO(data)).convert("RGB")
                    self.image_cache[url] = image
                    if url == self.image_url_current:
                        self._show_image(image)
                except Exception:
                    continue
        except queue.Empty:
            pass

    def open_magazine(self):
        path = filedialog.askopenfilename(
            parent=self, title="Open a magazine or newspaper PDF",
            filetypes=[("PDF magazines and newspapers", "*.pdf"), ("All files", "*.*")]
        )
        if not path:
            return
        if fitz is None or Image is None or ImageTk is None:
            messagebox.showerror(
                "PDF reader unavailable",
                "Install the updated app packages with:\npy -m pip install -r requirements.txt",
                parent=self,
            )
            return
        try:
            document = fitz.open(path)
            if document.page_count == 0:
                document.close()
                raise ValueError("This PDF has no pages")
        except Exception as exc:
            messagebox.showerror("Could not open magazine", str(exc), parent=self)
            return

        from pathlib import Path
        viewer = tk.Toplevel(self)
        viewer.title(f"Flip Book · {Path(path).name}")
        viewer.geometry("1050x790")
        viewer.minsize(650, 500)
        viewer.configure(bg="#10151d")
        state = {"page": 0, "photo": None, "resize_job": None}
        canvas = tk.Canvas(viewer, bg="#080c12", highlightthickness=0)
        canvas.pack(fill="both", expand=True, padx=12, pady=(12, 5))
        controls = tk.Frame(viewer, bg="#141e28", padx=12, pady=10)
        controls.pack(fill="x", padx=12, pady=(0, 12))
        page_label = tk.Label(controls, text="", bg="#141e28", fg=self.TEXT,
                              font=("Segoe UI", 10, "bold"))
        page_label.pack(side="left", expand=True)

        def render_page():
            if not viewer.winfo_exists():
                return
            page = document.load_page(state["page"])
            width = max(canvas.winfo_width() - 60, 400)
            height = max(canvas.winfo_height() - 40, 400)
            scale = min(width / page.rect.width, height / page.rect.height, 1.8)
            pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale),
                                     colorspace=fitz.csRGB, alpha=False)
            rendered = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
            state["photo"] = ImageTk.PhotoImage(rendered)
            canvas.delete("all")
            canvas.create_image(canvas.winfo_width() // 2, canvas.winfo_height() // 2,
                                image=state["photo"], anchor="center")
            page_label.configure(text=f"PAGE  {state['page'] + 1}  /  {document.page_count}")

        def turn_page(step):
            state["page"] = (state["page"] + step) % document.page_count
            render_page()

        tk.Button(controls, text="◀ Previous", command=lambda: turn_page(-1),
                  bg="#202b38", fg=self.TEXT, relief="flat", bd=0,
                  padx=12, pady=8).pack(side="left")
        tk.Button(controls, text="Next ▶", command=lambda: turn_page(1),
                  bg="#278656", fg=self.TEXT, relief="flat", bd=0,
                  padx=12, pady=8).pack(side="right")

        def resized(_event=None):
            if state["resize_job"]:
                try:
                    viewer.after_cancel(state["resize_job"])
                except tk.TclError:
                    pass
            state["resize_job"] = viewer.after(160, render_page)

        canvas.bind("<Configure>", resized)
        viewer.bind("<Left>", lambda _event: turn_page(-1))
        viewer.bind("<Right>", lambda _event: turn_page(1))
        viewer.focus_set()
        viewer.protocol("WM_DELETE_WINDOW", lambda: (document.close(), viewer.destroy()))
        viewer.after(180, render_page)

    def close(self):
        self.closed = True

