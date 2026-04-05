#!/bin/bash
set -u

PIDFILE="$HOME/radio/run/ham-radio-de-luxe.pid"
LOGFILE="$HOME/radio/logs/ham-radio-de-luxe.log"
mkdir -p "$HOME/radio/run" "$HOME/radio/logs"

if [ -f "$PIDFILE" ]; then
  PID="$(cat "$PIDFILE")"
  if kill -0 "$PID" 2>/dev/null; then
    echo "Ham Radio de Luxe ya estaba activo"
    exit 0
  fi
  rm -f "$PIDFILE"
fi

COMMAND=$(cat <<'__RADIO_CMD__'
env WINEPREFIX="/home/ramon/.wine-hrd" wine-stable C:\\users\\Public\\Desktop\\Ham\ Radio\ Deluxe.lnk
__RADIO_CMD__
)

nohup bash -lc "$COMMAND" >>"$LOGFILE" 2>&1 &
PID=$!
echo "$PID" > "$PIDFILE"

sleep 2

if kill -0 "$PID" 2>/dev/null; then
  echo "Ham Radio de Luxe arrancado. PID=$PID"
  exit 0
fi

echo "ERROR: Ham Radio de Luxe no arrancó"
rm -f "$PIDFILE"
exit 1
