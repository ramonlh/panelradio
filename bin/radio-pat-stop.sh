#!/bin/bash

PAT_PID_FILE="/home/ramon/radio/run/pat.pid"
PAT_LOG="/home/ramon/radio/logs/pat.log"

PID=""
if [ -f "$PAT_PID_FILE" ]; then
  PID=$(cat "$PAT_PID_FILE" 2>/dev/null)
fi

if [ -z "$PID" ]; then
  PID=$(pgrep -xo -f 'pat http')
fi

if [ -n "$PID" ]; then
  kill "$PID" 2>/dev/null || true
fi

for i in $(seq 1 10); do
  sleep 1
  if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
    :
  else
    break
  fi
done

if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
  kill -9 "$PID" 2>/dev/null || true
fi

rm -f "$PAT_PID_FILE"

if pgrep -xo -f 'pat http' >/dev/null; then
  /home/ramon/radio/bin/radio-show-status.sh \
    error \
    "PAT Winlink" \
    "ERROR" \
    "no se pudo cerrar ; PID=$PID" \
    "$PAT_LOG"
  exit 1
else
  /home/ramon/radio/bin/radio-show-status.sh \
    ok \
    "PAT Winlink" \
    "OK" \
    "cerrado ; PID=$PID"
  exit 0
fi
