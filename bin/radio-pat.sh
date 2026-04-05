#!/bin/bash

CFG="/home/ramon/radio/conf/radio.env"
[ -f "$CFG" ] && source "$CFG"

PAT_URL="${PAT_URL:-http://127.0.0.1:8080}"
PAT_CMD="${PAT_CMD:-pat http}"
PAT_LOG="/home/ramon/radio/logs/pat.log"
PAT_PID_FILE="/home/ramon/radio/run/pat.pid"

mkdir -p /home/ramon/radio/logs /home/ramon/radio/run

if /home/ramon/radio/bin/radio-pat-status.sh; then
  PID=$(cat "$PAT_PID_FILE" 2>/dev/null)
  xdg-open "$PAT_URL" >/dev/null 2>&1 &
  /home/ramon/radio/bin/radio-show-status.sh \
    ok \
    "PAT Winlink" \
    "OK" \
    "PAT=$PID ; url=$PAT_URL"

  while /home/ramon/radio/bin/radio-pat-status.sh; do
    sleep 2
  done
  exit 0
fi

/home/ramon/radio/bin/radio-stop-no-pat.sh >/dev/null 2>&1 || true
sleep 1

: > "$PAT_LOG"

/bin/bash -lc "exec $PAT_CMD" >>"$PAT_LOG" 2>&1 &
PAT_PID=$!
echo "$PAT_PID" > "$PAT_PID_FILE"

OK=0
for i in $(seq 1 20); do
  sleep 1
  if kill -0 "$PAT_PID" 2>/dev/null; then
    if ss -ltnp 2>/dev/null | grep -F ':8080' | grep -F "\"pat\",pid=$PAT_PID" >/dev/null; then
      OK=1
      break
    fi
  else
    break
  fi
done

if [ "$OK" -eq 1 ]; then
  xdg-open "$PAT_URL" >/dev/null 2>&1 &
  /home/ramon/radio/bin/radio-show-status.sh \
    ok \
    "PAT Winlink" \
    "OK" \
    "PAT=$PAT_PID ; url=$PAT_URL"

  while /home/ramon/radio/bin/radio-pat-status.sh; do
    sleep 2
  done

  exit 0
else
  /home/ramon/radio/bin/radio-show-status.sh \
    error \
    "PAT Winlink" \
    "ERROR" \
    "PAT=$PAT_PID ; url=$PAT_URL" \
    "$PAT_LOG"
  rm -f "$PAT_PID_FILE"
  exit 1
fi
