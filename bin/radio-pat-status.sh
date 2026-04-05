#!/bin/bash

PAT_PID_FILE="/home/ramon/radio/run/pat.pid"

if [ -f "$PAT_PID_FILE" ]; then
  PID=$(cat "$PAT_PID_FILE" 2>/dev/null)
  if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
    CMD=$(ps -p "$PID" -o args= 2>/dev/null)
    case "$CMD" in
      *"pat http"*)
        exit 0
        ;;
    esac
  fi
  rm -f "$PAT_PID_FILE"
fi

PID=$(pgrep -xo -f 'pat http')
if [ -n "$PID" ]; then
  echo "$PID" > "$PAT_PID_FILE"
  exit 0
fi

exit 1
