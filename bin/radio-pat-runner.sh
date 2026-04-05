#!/bin/bash

CFG="/home/ramon/radio/conf/radio.env"
[ -f "$CFG" ] && source "$CFG"

PAT_CMD="${PAT_CMD:-pat http}"
PAT_LOG="/home/ramon/radio/logs/pat.log"
PAT_PID_FILE="/home/ramon/radio/run/pat.pid"

mkdir -p /home/ramon/radio/logs /home/ramon/radio/run

echo $$ > "$PAT_PID_FILE"
trap 'rm -f "$PAT_PID_FILE"' EXIT

exec >>"$PAT_LOG" 2>&1
echo
echo "============================================================"
echo "Arranque PAT: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Comando     : $PAT_CMD"
echo "============================================================"

exec bash -lc "exec $PAT_CMD"
