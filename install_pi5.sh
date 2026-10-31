#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
APP_HOME="${HOME}/SURAKMediaCenterPi5"
DESKTOP_DIR="${HOME}/.local/share/applications"
DESKTOP_FILE="${DESKTOP_DIR}/surak-media-center-pi5.desktop"

if ! command -v apt-get >/dev/null 2>&1; then
    echo "This installer supports Raspberry Pi OS and Debian-based Linux." >&2
    exit 1
fi

echo "Installing the media player and Python interface packages..."
sudo apt-get update
sudo apt-get install -y python3 python3-tk vlc python3-vlc python3-pil python3-pil.imagetk fonts-dejavu-core

PDF_PACKAGE=()
if apt-cache show python3-pymupdf >/dev/null 2>&1; then
    PDF_PACKAGE=(python3-pymupdf)
elif apt-cache show python3-fitz >/dev/null 2>&1; then
    PDF_PACKAGE=(python3-fitz)
fi
if ((${#PDF_PACKAGE[@]})); then
    sudo apt-get install -y "${PDF_PACKAGE[@]}"
else
    echo "PDF reader package unavailable; other features will work normally."
fi

mkdir -p "$APP_HOME" "$DESKTOP_DIR"
for file in media_center_linux_pi5.py radio_app.py radio_map_windows.py \
            live_tv_windows.py magazine_reader.py countries.geojson; do
    install -m 644 "$SOURCE_DIR/$file" "$APP_HOME/$file"
done
for file in favorites.json map_favorites.json surak_home_tv_favorites.json; do
    if [[ ! -e "$APP_HOME/$file" && -e "$SOURCE_DIR/$file" ]]; then
        install -m 644 "$SOURCE_DIR/$file" "$APP_HOME/$file"
    fi
done

cat > "$APP_HOME/run_media_center_pi5.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
exec python3 media_center_linux_pi5.py "$@"
EOF
chmod 755 "$APP_HOME/run_media_center_pi5.sh"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=SURAK Media Center Pi 5
Comment=Full radio, live TV, news, and magazines
Exec="$APP_HOME/run_media_center_pi5.sh"
Icon=audio-radio
Terminal=false
Categories=AudioVideo;Audio;Video;News;
EOF
chmod 644 "$DESKTOP_FILE"

echo
echo "Installed. Open SURAK Media Center Pi 5 from the Raspberry Pi menu."
echo "Or launch: $APP_HOME/run_media_center_pi5.sh"
