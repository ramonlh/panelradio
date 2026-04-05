#!/bin/bash

/home/ramon/radio/bin/radio-stop.sh
sleep 1
mkdir -p /home/ramon/radio/logs

wsjtx >/home/ramon/radio/logs/wsjtx.log 2>&1 &
WSJT_PID=$!

sleep 3

if kill -0 "$WSJT_PID" 2>/dev/null; then
  /home/ramon/radio/bin/radio-show-status.sh \
    ok \
    "WSJT-X" \
    "OK" \
    "WSJT-X=$WSJT_PID"
  wait "$WSJT_PID"
  exit $?
else
  /home/ramon/radio/bin/radio-show-status.sh \
    error \
    "WSJT-X" \
    "ERROR" \
    "WSJT-X=$WSJT_PID" \
    /home/ramon/radio/logs/wsjtx.log
  exit 1
fi
