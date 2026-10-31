#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
APP_HOME="${HOME}/SURAKMediaCenterPi5"

if [[ ! -d "$APP_HOME" ]]; then
    echo "SURAK Media Center Pi 5 is not installed. Run install_pi5.sh first." >&2
    exit 1
fi

for file in media_center_linux_pi5.py radio_app.py radio_map_windows.py \
            live_tv_windows.py magazine_reader.py countries.geojson; do
    install -m 644 "$SOURCE_DIR/$file" "$APP_HOME/$file"
done
echo "Pi 5 edition updated. Saved favorites have been kept."
