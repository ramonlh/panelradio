#!/bin/bash

/home/ramon/radio/bin/radio-stop.sh
sleep 1
mkdir -p /home/ramon/radio/logs

direwolf -c /home/ramon/radio/conf/direwolf.conf \
  >/home/ramon/radio/logs/direwolf.log 2>&1 &
DW_PID=$!

sleep 2

java -jar /home/ramon/YAAC/YAAC.jar \
  >/home/ramon/radio/logs/yaac.log 2>&1 &
YAAC_PID=$!

sleep 3

if kill -0 "$DW_PID" 2>/dev/null && kill -0 "$YAAC_PID" 2>/dev/null; then
  /home/ramon/radio/bin/radio-show-status.sh \
    ok \
    "APRS (Dire Wolf + YAAC)" \
    "OK" \
    "Dire Wolf=$DW_PID ; YAAC=$YAAC_PID"
  wait "$YAAC_PID"
  RC=$?
else
  /home/ramon/radio/bin/radio-show-status.sh \
    error \
    "APRS (Dire Wolf + YAAC)" \
    "ERROR" \
    "Dire Wolf=$DW_PID ; YAAC=$YAAC_PID" \
    /home/ramon/radio/logs/direwolf.log \
    /home/ramon/radio/logs/yaac.log
  kill "$DW_PID" 2>/dev/null || true
  kill "$YAAC_PID" 2>/dev/null || true
  exit 1
fi

kill "$DW_PID" 2>/dev/null || true
wait "$DW_PID" 2>/dev/null || true
exit $RC
