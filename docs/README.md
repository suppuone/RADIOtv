# COOLmagRaTv 4.0

This is the GitHub Pages version of COOLmagRaTv. The app combines internet radio, live TV, favorites, recent history, news links, and responsive playback controls.

## Version 4 change: shared radio and TV favorites

Open **Settings → Shared station & channel library → Open Admin Panel**. The standalone admin page opens in a new browser tab. Connect with a GitHub fine-grained token limited to `suppuone/RADIOtv` and **Contents: Read and write** permission. Choose **TV channels** or **Radio stations** to manage the corresponding public list:

- TV favorites: `surak_home_tv_favorites.json`
- Radio favorites: `map_favorites.json`

The two lists publish independently, so editing one does not overwrite the other. In the admin tab you can add entries, edit names, countries, categories, stream and logo URLs, remove entries, search, import browser favorites or JSON, and download a JSON backup. Use **Publish shared list** to write the selected list to the repository. Your token is held only in that tab's memory and cleared when you disconnect or close the tab. Visitors receive shared additions or edits when the app refreshes.

## Features

- Radio Browser station discovery, country selection, and personal radio favorites.
- Music, News, Talks, and Others buttons filter the current radio list; choose Favorites to curate saved stations by genre.
- Favorites opens the TV list directly and switches between Radio and TV with icon tabs, remembering the last selection.
- IPTV-org live channel browsing, country filtering, and personal TV favorites.
- Shared radio and TV favorite lists managed from Settings.
- Recent streams, news links, phone-friendly cards, fullscreen TV, and player controls.
- Light, Night, and E-paper themes; optional local time and weather controls.
- Ctrl+K / ⌘K quick search; Space play/pause, M mute, F fullscreen in TV mode.

## Open locally

From this folder, run:

```text
python -m http.server 8000
```

Then visit `http://localhost:8000`.

Stream availability, picture quality, and browser compatibility depend on each broadcaster and provider.
