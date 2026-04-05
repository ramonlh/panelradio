#!/bin/bash
set -e

SONDEHUB_URL="https://sondehub.org/#!mt=Mapnik&mz=13&qm=3h&mc=40.4393,-3.69587"
LOCAL_URL="http://127.0.0.1:5000/"

open_url_new_window() {
    local url="$1"

    if command -v firefox >/dev/null 2>&1; then
        setsid -f firefox --new-window "$url" >/dev/null 2>&1
        return 0
    fi

    if command -v chromium >/dev/null 2>&1; then
        setsid -f chromium --new-window "$url" >/dev/null 2>&1
        return 0
    fi

    if command -v chromium-browser >/dev/null 2>&1; then
        setsid -f chromium-browser --new-window "$url" >/dev/null 2>&1
        return 0
    fi

    if command -v google-chrome >/dev/null 2>&1; then
        setsid -f google-chrome --new-window "$url" >/dev/null 2>&1
        return 0
    fi

    if command -v brave-browser >/dev/null 2>&1; then
        setsid -f brave-browser --new-window "$url" >/dev/null 2>&1
        return 0
    fi

    setsid -f xdg-open "$url" >/dev/null 2>&1
}

~/radio/bin/radio-stop.sh
sleep 1
mkdir -p ~/radio/logs

cd ~/radiosonde_auto_rx/auto_rx
nohup python3 auto_rx.py > ~/radio/logs/autorx.log 2>&1 &

# Abrir primero Sondehub
open_url_new_window "$SONDEHUB_URL"

# Dar tiempo REAL a que el navegador termine de abrir esa ventana
sleep 8

# Esperar a que la web local esté disponible
for i in {1..30}; do
    if command -v curl >/dev/null 2>&1; then
        if curl -fsS "$LOCAL_URL" >/dev/null 2>&1; then
            break
        fi
    fi
    sleep 1
done

# Abrir después la web local en otra ventana nueva
open_url_new_window "$LOCAL_URL"
