#!/bin/bash

CFG="/home/ramon/radio/conf/radio.env"
ICONO="/home/ramon/radio/iconos/radio.svg"

mkdir -p /home/ramon/radio/conf

get_cfg() {
  local key="$1"
  local def="$2"
  local line
  local val

  line=$(grep -E "^${key}=" "$CFG" 2>/dev/null | tail -n1)

  if [ -z "$line" ]; then
    printf '%s' "$def"
    return
  fi

  val=${line#*=}
  val=${val#\"}
  val=${val%\"}

  printf '%s' "$val"
}

# Protege valores que empiezan por '-' para que yad no los confunda con opciones
form_safe() {
  case "$1" in
    -*) printf ' %s' "$1" ;;
    *)  printf '%s' "$1" ;;
  esac
}

# Quita espacios de protección al principio y al final
trim_ws() {
  local v="$1"
  v="${v#"${v%%[![:space:]]*}"}"
  v="${v%"${v##*[![:space:]]}"}"
  printf '%s' "$v"
}

if [ ! -f "$CFG" ]; then
  cat > "$CFG" <<EOCFG
CALLSIGN="EA4GZI"
APRS_SSID="9"
LAT="40.4168"
LON="-3.7038"
LOCATOR="IN80"
COMMENT="Home station"
AUDIO_DEV="default"
AGW_PORT="8000"
KISS_PORT="8001"
YAAC_JAR="/home/ramon/YAAC/YAAC.jar"
PAT_CMD="pat http"
PAT_TITLE="PAT Winlink"
PAT_URL="http://127.0.0.1:8080"
EOCFG
fi

CALLSIGN=$(get_cfg "CALLSIGN" "EA4GZI")
APRS_SSID=$(get_cfg "APRS_SSID" "9")
LAT=$(get_cfg "LAT" "40.4168")
LON=$(get_cfg "LON" "-3.7038")
LOCATOR=$(get_cfg "LOCATOR" "IN80")
COMMENT=$(get_cfg "COMMENT" "Home station")
AUDIO_DEV=$(get_cfg "AUDIO_DEV" "default")
AGW_PORT=$(get_cfg "AGW_PORT" "8000")
KISS_PORT=$(get_cfg "KISS_PORT" "8001")
YAAC_JAR=$(get_cfg "YAAC_JAR" "/home/ramon/YAAC/YAAC.jar")
PAT_CMD=$(get_cfg "PAT_CMD" "pat http")
PAT_TITLE=$(get_cfg "PAT_TITLE" "PAT Winlink")
PAT_URL=$(get_cfg "PAT_URL" "http://127.0.0.1:8080")

RESPUESTA=$(yad --form \
  --title="Configuración de estación" \
  --window-icon="$ICONO" \
  --image="$ICONO" \
  --image-on-top \
  --text="Introduce los parámetros comunes de la estación" \
  --width=780 \
  --height=620 \
  --center \
  --field="Indicativo" "$(form_safe "$CALLSIGN")" \
  --field="SSID APRS" "$(form_safe "$APRS_SSID")" \
  --field="Latitud" "$(form_safe "$LAT")" \
  --field="Longitud" "$(form_safe "$LON")" \
  --field="Locator" "$(form_safe "$LOCATOR")" \
  --field="Comentario" "$(form_safe "$COMMENT")" \
  --field="Audio RX/TX" "$(form_safe "$AUDIO_DEV")" \
  --field="Puerto AGW" "$(form_safe "$AGW_PORT")" \
  --field="Puerto KISS" "$(form_safe "$KISS_PORT")" \
  --field="Ruta YAAC JAR" "$(form_safe "$YAAC_JAR")" \
  --field="Comando PAT" "$(form_safe "$PAT_CMD")" \
  --field="Título ventana PAT" "$(form_safe "$PAT_TITLE")" \
  --field="URL PAT" "$(form_safe "$PAT_URL")" \
  --separator="|")

RC=$?
[ $RC -ne 0 ] && exit 0

IFS="|" read -r \
  CALLSIGN \
  APRS_SSID \
  LAT \
  LON \
  LOCATOR \
  COMMENT \
  AUDIO_DEV \
  AGW_PORT \
  KISS_PORT \
  YAAC_JAR \
  PAT_CMD \
  PAT_TITLE \
  PAT_URL <<< "$RESPUESTA"

CALLSIGN=$(trim_ws "$CALLSIGN")
APRS_SSID=$(trim_ws "$APRS_SSID")
LAT=$(trim_ws "$LAT")
LON=$(trim_ws "$LON")
LOCATOR=$(trim_ws "$LOCATOR")
COMMENT=$(trim_ws "$COMMENT")
AUDIO_DEV=$(trim_ws "$AUDIO_DEV")
AGW_PORT=$(trim_ws "$AGW_PORT")
KISS_PORT=$(trim_ws "$KISS_PORT")
YAAC_JAR=$(trim_ws "$YAAC_JAR")
PAT_CMD=$(trim_ws "$PAT_CMD")
PAT_TITLE=$(trim_ws "$PAT_TITLE")
PAT_URL=$(trim_ws "$PAT_URL")

cat > "$CFG" <<EOCFG
CALLSIGN="$CALLSIGN"
APRS_SSID="$APRS_SSID"
LAT="$LAT"
LON="$LON"
LOCATOR="$LOCATOR"
COMMENT="$COMMENT"
AUDIO_DEV="$AUDIO_DEV"
AGW_PORT="$AGW_PORT"
KISS_PORT="$KISS_PORT"
YAAC_JAR="$YAAC_JAR"
PAT_CMD="$PAT_CMD"
PAT_TITLE="$PAT_TITLE"
PAT_URL="$PAT_URL"
EOCFG

/home/ramon/radio/bin/radio-generate-configs.sh

yad --info \
  --title="Radio" \
  --window-icon="$ICONO" \
  --text="Configuración guardada correctamente." \
  --width=360
