# SURAK Media Center — Raspberry Pi 5 edition

This is a separate full-featured Linux build for Raspberry Pi 5. It does not change the existing `web_radio` folder or the lightweight Pi edition.

## Features

- Country-clickable world radio map, Radio Browser/IPRD/Verified Radio choices, station favorites, weather details, country clock, news tickers, volume, and audio meter.
- Live TV channel cards, categories, channel favorites, fullscreen playback, aspect controls, volume, and Bluetooth media keys when Raspberry Pi OS sends standard media key events.
- News feeds with article images and publisher pages, custom RSS feeds, and local PDF magazines with page turning (when the OS supplies the PyMuPDF package).
- One window with RADIO MAP, LIVE TV, and NEWS & MAGAZINES switches. Leaving radio or TV stops playback.

## Install on Raspberry Pi 5

1. Copy this entire `web_radio_pi5` folder to the Pi, for example onto its Desktop.
2. Open Terminal in the copied folder.
3. Run:

   ```bash
   bash install_pi5.sh
   ```

   Enter the Pi password when asked. The installer adds the required Raspberry Pi OS packages and creates a menu entry named **SURAK Media Center Pi 5**.

4. Launch it from the Pi menu, or run:

   ```bash
   ~/SURAKMediaCenterPi5/run_media_center_pi5.sh
   ```

For a later code update, copy the new folder and run `bash update_pi5.sh`; it does not reinstall packages or overwrite saved favorites. The full edition uses more graphics and TV logo downloads than the lightweight Pi edition. For smooth playback, use Raspberry Pi OS Desktop and a stable network; choosing a lower-resolution stream can help when a broadcaster's HD feed is choppy.

Audio can use a Bluetooth speaker selected in Raspberry Pi sound settings, or the Pi's 3.5 mm jack connected to a powered speaker/amplifier. A passive speaker needs an amplifier.
