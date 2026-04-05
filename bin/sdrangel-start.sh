#!/bin/bash
set -u

PIDFILE="$HOME/radio/run/sdrangel.pid"
LOGFILE="$HOME/radio/logs/sdrangel.log"
mkdir -p "$HOME/radio/run" "$HOME/radio/logs"

if [ -f "$PIDFILE" ]; then
  PID="$(cat "$PIDFILE")"
  if kill -0 "$PID" 2>/dev/null; then
    echo "SDRAngel ya estaba activo"
    exit 0
  fi
  rm -f "$PIDFILE"
fi

COMMAND=$(cat <<'__RADIO_CMD__'
sdrangel
__RADIO_CMD__
)

nohup bash -lc "$COMMAND" >>"$LOGFILE" 2>&1 &
PID=$!
echo "$PID" > "$PIDFILE"

sleep 2

if kill -0 "$PID" 2>/dev/null; then
  echo "SDRAngel arrancado. PID=$PID"
  exit 0
fi

echo "ERROR: SDRAngel no arrancó"
rm -f "$PIDFILE"
exit 1
