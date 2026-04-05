#!/bin/bash

ICONO="/home/ramon/radio/iconos/radio.svg"

while true; do
  if /home/ramon/radio/bin/radio-pat-status.sh; then
    OPCION=$(yad --list \
      --title="Menú de radio - PAT activo" \
      --center \
      --window-icon="$ICONO" \
      --image="$ICONO" \
      --image-on-top \
      --text="PAT está activo.\n\nLas demás opciones quedan bloqueadas hasta cerrarlo." \
      --text-align=center \
      --no-headers \
      --separator="" \
      --print-column=1 \
      --column="ID:HD" \
      --column="Opciones disponibles:TEXT" \
      "pat_open" "PAT activo    — abrir navegador" \
      "pat_stop" "PAT activo    — cerrar PAT" \
      "exit"     "Salir" \
      --width=720 \
      --height=420 \
      --button="Abrir:0" \
      --button="Salir:1" \
      --buttons-layout=center)
    RC=$?
    [ $RC -ne 0 ] && exit 0

    case "$OPCION" in
      pat_open)
        CFG="/home/ramon/radio/conf/radio.env"
        [ -f "$CFG" ] && source "$CFG"
        PAT_URL="${PAT_URL:-http://127.0.0.1:8080}"
        xdg-open "$PAT_URL" >/dev/null 2>&1 &
        ;;
      pat_stop)
        /home/ramon/radio/bin/radio-pat-stop.sh
        ;;
      exit)
        exit 0
        ;;
    esac
  else
    OPCION=$(yad --list \
      --title="Menú de radio" \
      --center \
      --window-icon="$ICONO" \
      --image="$ICONO" \
      --image-on-top \
      --text="Estación de radioafición\n\nSelecciona una opción" \
      --text-align=center \
      --no-headers \
      --separator="" \
      --print-column=1 \
      --column="ID:HD" \
      --column="Opciones disponibles:TEXT" \
      "config"  "Configurar estación" \
      "aprs"    "APRS        — Dire Wolf + YAAC" \
      "digital" "Digital     — fldigi + flrig" \
      "wsjt"    "FT8 / FT4   — WSJT-X" \
      "pat"     "Winlink     — PAT" \
      "stop"    "Parar todo" \
      "exit"    "Salir" \
      --width=720 \
      --height=540 \
      --button="Abrir:0" \
      --button="Salir:1" \
      --buttons-layout=center)
    RC=$?
    [ $RC -ne 0 ] && exit 0

    case "$OPCION" in
      config)
        /home/ramon/radio/bin/radio-settings.sh
        ;;
      aprs)
        /home/ramon/radio/bin/radio-aprs.sh
        ;;
      digital)
        /home/ramon/radio/bin/radio-fldigi.sh
        ;;
      wsjt)
        /home/ramon/radio/bin/radio-wsjtx.sh
        ;;
      pat)
        /home/ramon/radio/bin/radio-pat.sh
        ;;
      stop)
        /home/ramon/radio/bin/radio-stop.sh
        ;;
      exit)
        exit 0
        ;;
    esac
  fi
done
