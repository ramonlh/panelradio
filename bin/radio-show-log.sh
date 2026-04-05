#!/bin/bash

TITULO="$1"
shift

emit_panel() {
  echo "$TITULO"
  echo
  for LOG in "$@"; do
    echo "============================================================"
    echo "LOG: $LOG"
    echo "============================================================"
    if [ -f "$LOG" ]; then
      tail -n 30 "$LOG"
    else
      echo "No existe ese fichero."
    fi
    echo
  done
}

if [ "${RADIO_PANEL_MODE:-0}" = "1" ]; then
  emit_panel "$@"
  exit 0
fi

TMP=$(mktemp /tmp/radio-log-XXXXXX.txt)

{
  emit_panel "$@"
} > "$TMP"

yad --text-info \
  --title="Radio - detalle del arranque" \
  --window-icon="/home/ramon/radio/iconos/radio.svg" \
  --filename="$TMP" \
  --width=780 \
  --height=520 \
  --button="Cerrar:0"

rm -f "$TMP"
