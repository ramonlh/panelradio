#!/bin/bash

TIPO="$1"          # ok | error
PROGRAMA="$2"      # texto
ESTADO="$3"        # OK | ERROR
PIDS="$4"          # texto con pids
shift 4

emit_panel() {
  echo "Fecha y hora : $(date '+%Y-%m-%d %H:%M:%S')"
  echo "Programa     : $PROGRAMA"
  echo "Estado       : $ESTADO"
  echo "PID(s)       : $PIDS"
  echo

  if [ "$TIPO" = "error" ]; then
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
  fi
}

if [ "${RADIO_PANEL_MODE:-0}" = "1" ]; then
  emit_panel "$@"
  exit 0
fi

TMP=$(mktemp /tmp/radio-status-XXXXXX.txt)

{
  emit_panel "$@"
} > "$TMP"

if [ "$TIPO" = "ok" ]; then
  yad --text-info \
    --title="Radio - arranque correcto" \
    --window-icon="/home/ramon/radio/iconos/radio.svg" \
    --filename="$TMP" \
    --width=520 \
    --height=260 \
    --timeout=2 \
    --no-buttons
else
  yad --text-info \
    --title="Radio - fallo de arranque" \
    --window-icon="/home/ramon/radio/iconos/radio.svg" \
    --filename="$TMP" \
    --width=820 \
    --height=560 \
    --button="Cerrar:0"
fi

rm -f "$TMP"
