#!/bin/bash
set -u

PIDFILE="$HOME/radio/run/wfview.pid"

if [ -f "$PIDFILE" ]; then
  PID="$(cat "$PIDFILE")"
  if kill -0 "$PID" 2>/dev/null; then
    kill "$PID" 2>/dev/null || true
    sleep 2
    if kill -0 "$PID" 2>/dev/null; then
      kill -9 "$PID" 2>/dev/null || true
    fi
  fi
  rm -f "$PIDFILE"
fi

if "$HOME/radio/bin/wfview-status.sh" >/dev/null 2>&1; then
  echo "ERROR: WFview sigue activo"
  exit 1
fi

echo "WFview parado"
exit 0
