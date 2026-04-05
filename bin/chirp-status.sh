#!/bin/bash
set -u

PIDFILE="$HOME/radio/run/chirp.pid"

if [ -f "$PIDFILE" ]; then
  PID="$(cat "$PIDFILE")"
  if kill -0 "$PID" 2>/dev/null; then
    echo "activo"
    exit 0
  fi
  rm -f "$PIDFILE"
fi

echo "parado"
exit 1
