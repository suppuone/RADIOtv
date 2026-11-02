# COOLmagRaTv 2.0

This is a separate redesign of the browser media center. It uses the existing Radio Browser and IPTV-org sources, HLS playback, station favorites, TV favorites, recent history, and weather lookups. The original `web_radio/docs` site is unchanged.

## Highlights

- Cinematic 12-column Home dashboard with BBC Live hero, weather, and region tiles.
- Floating glass playback dock with volume and mute controls.
- Animated loading skeletons and smooth view changes.
- Quick search with **Ctrl+K** (Windows/Linux) or **⌘K** (Mac); use arrow keys and Enter.
- **Space** toggles play/pause, **M** toggles mute, and **F** toggles TV fullscreen while on Live TV.
- Cinema Mode is available from the TV video controls.
- Settings include Light, Night, and E-paper themes, plus Weather, Local time, and Volume switches. Weather and time start off; audio starts on at 30% volume on a fresh install. Choices are saved on the device.
- Settings includes **Check for updates**, which checks the currently hosted copy and reloads it when a newer app version is published. Increment `APP_VERSION` in `app.js` with each release so the button can detect it.
- Responsive layout for desktop, tablet, and phone.
- Live TV can load worldwide or by country using the country selector. Radio library cards use the same compact image-card style as TV.
- Opening Radio shows saved favorites first when any are available; Refresh or Search returns to the station list.

## Open locally

Because the app fetches radio, TV, and weather data, open it through a local web server rather than double-clicking `index.html`. From this folder, run:

```text
python -m http.server 8000
```

Then open `http://localhost:8000` in your browser.

## Publish separately

This version is in its own folder and is not published to GitHub Pages automatically. To make it the live site, copy these four files into the repository's configured Pages folder or update the Pages publishing source. Keep a backup of the current site before replacing its files.

An optional live-user number appears only when Supabase Realtime Presence is configured in `app.js`; without it, no placeholder tile is shown.

Stream availability and browser compatibility depend on each broadcaster and provider.
