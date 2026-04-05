#!/bin/bash

/home/ramon/radio/bin/radio-stop.sh
sleep 1
mkdir -p /home/ramon/radio/logs

flrig >/home/ramon/radio/logs/flrig.log 2>&1 &
FLRIG_PID=$!

sleep 2

fldigi >/home/ramon/radio/logs/fldigi.log 2>&1 &
FLDIGI_PID=$!

sleep 3

if kill -0 "$FLRIG_PID" 2>/dev/null && kill -0 "$FLDIGI_PID" 2>/dev/null; then
  /home/ramon/radio/bin/radio-show-status.sh \
    ok \
    "Digital (flrig + fldigi)" \
    "OK" \
    "flrig=$FLRIG_PID ; fldigi=$FLDIGI_PID"
  wait "$FLDIGI_PID"
  RC=$?
else
  /home/ramon/radio/bin/radio-show-status.sh \
    error \
    "Digital (flrig + fldigi)" \
    "ERROR" \
    "flrig=$FLRIG_PID ; fldigi=$FLDIGI_PID" \
    /home/ramon/radio/logs/flrig.log \
    /home/ramon/radio/logs/fldigi.log
  kill "$FLRIG_PID" 2>/dev/null || true
  kill "$FLDIGI_PID" 2>/dev/null || true
  exit 1
fi

kill "$FLRIG_PID" 2>/dev/null || true
wait "$FLRIG_PID" 2>/dev/null || true
exit $RC
