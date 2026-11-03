# COOLmagRaTv 4.0

This is the GitHub Pages version of COOLmagRaTv. The app combines internet radio, live TV, favorites, recent history, news links, and responsive playback controls.

## Version 4 change: shared radio and TV favorites

Open **Settings → Shared favorites → Admin**. Connect with a GitHub fine-grained token that has **Contents: Read and write** access to the `suppuone/RADIOtv` repository. Choose **TV channels** or **Radio stations** to edit the corresponding public list:

- TV favorites: `surak_home_tv_favorites.json`
- Radio favorites: `map_favorites.json`

The two lists publish independently, so editing one does not overwrite the other. The **Import browser favorites** button imports favorites from the current site origin; localhost and GitHub Pages keep separate browser storage. Use **Publish shared list** to write the selected list to the repository. Visitors receive shared additions or edits when the app refreshes.

## Features

- Radio Browser station discovery, country selection, and personal radio favorites.
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
