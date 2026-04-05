#!/bin/bash

pkill -x direwolf 2>/dev/null || true
pkill -f 'java -jar /home/ramon/YAAC/YAAC.jar' 2>/dev/null || true
pkill -x fldigi 2>/dev/null || true
pkill -x flrig 2>/dev/null || true
pkill -x wsjtx 2>/dev/null || true
pkill -f auto_rx.py 2>/dev/null || true

exit 0
