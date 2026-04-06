#!/usr/bin/env python3
import json
import os
import re
import subprocess
import threading
import time
import unicodedata
from pathlib import Path
from typing import Any

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, GLib, Gtk

APP_DIR = Path.home() / "radio"
BIN_DIR = APP_DIR / "bin"
CONF_DIR = APP_DIR / "conf"
LOG_DIR = APP_DIR / "logs"
ICON_DIR = APP_DIR / "iconos"
RADIO_ENV = CONF_DIR / "radio.env"
ACTIONS_JSON = CONF_DIR / "actions.json"
RESOURCES_JSON = CONF_DIR / "resources.json"
WEBS_JSON = CONF_DIR / "web_links.json"
ICON_PATH = ICON_DIR / "radio.svg"

DEFAULT_ENV = {
    "CALLSIGN": "EA4GZI",
    "APRS_SSID": "9",
    "LAT": "40.4168",
    "LON": "-3.7038",
    "LOCATOR": "IN80",
    "COMMENT": "Home station",
    "AUDIO_DEV": "default",
    "AGW_PORT": "8000",
    "KISS_PORT": "8001",
    "YAAC_JAR": str(Path.home() / "YAAC" / "YAAC.jar"),
    "PAT_CMD": "pat http",
    "PAT_TITLE": "PAT Winlink",
    "PAT_URL": "http://127.0.0.1:8080",
}

FIELD_SPECS = [
    ("CALLSIGN", "Indicativo"),
    ("APRS_SSID", "SSID APRS"),
    ("LAT", "Latitud"),
    ("LON", "Longitud"),
    ("LOCATOR", "Locator"),
    ("COMMENT", "Comentario"),
    ("AUDIO_DEV", "Audio RX/TX"),
    ("AGW_PORT", "Puerto AGW"),
    ("KISS_PORT", "Puerto KISS"),
    ("YAAC_JAR", "Ruta YAAC JAR"),
    ("PAT_CMD", "Comando PAT"),
    ("PAT_TITLE", "Título ventana PAT"),
    ("PAT_URL", "URL PAT"),
]

DEFAULT_RESOURCES = [
    {"id": "vhf_aprs", "title": "Equipo APRS VHF", "description": "Radio/interfaz usados por Dire Wolf + YAAC"},
    {"id": "hf_rig_audio", "title": "Audio equipo HF", "description": "Audio del equipo HF principal"},
    {"id": "hf_rig_cat", "title": "CAT equipo HF", "description": "Control CAT/CI-V del equipo HF principal"},
    {"id": "rtlsdr", "title": "Pincho RTL-SDR", "description": "Receptor SDR usado por radiosonda"},
]

DEFAULT_ACTIONS = [
    {
        "id": "aprs",
        "title": "APRS",
        "subtitle": "Dire Wolf + YAAC",
        "kind": "script",
        "script": str(BIN_DIR / "radio-aprs.sh"),
        "icon": "network-wireless-symbolic",
        "icon_path": str(ICON_DIR / "yaac.png"),
        "pat_allowed": False,
        "css": "aprs",
        "resources": ["vhf_aprs"],
    },
    {
        "id": "digital",
        "title": "Digital",
        "subtitle": "fldigi + flrig",
        "kind": "script",
        "script": str(BIN_DIR / "radio-fldigi.sh"),
        "icon": "audio-x-generic-symbolic",
        "icon_path": str(ICON_DIR / "fldigi.png"),
        "pat_allowed": False,
        "css": "digital",
        "resources": ["hf_rig_audio", "hf_rig_cat"],
    },
    {
        "id": "wsjt",
        "title": "WSJT-X",
        "subtitle": "FT8 / FT4 / WSPR",
        "kind": "script",
        "script": str(BIN_DIR / "radio-wsjtx.sh"),
        "icon": "media-playback-start-symbolic",
        "icon_path": str(ICON_DIR / "wsjtx.png"),
        "pat_allowed": False,
        "css": "wsjt",
        "resources": ["hf_rig_audio", "hf_rig_cat"],
    },
    {
        "id": "pat",
        "title": "PAT",
        "subtitle": "arrancar / parar Winlink",
        "kind": "toggle_pat",
        "script_start": str(BIN_DIR / "radio-pat.sh"),
        "command_stop": "pkill -x pat || true",
        "icon": "mail-send-receive-symbolic",
        "icon_path": str(ICON_DIR / "pat.png"),
        "pat_allowed": True,
        "css": "success",
    },
    {
        "id": "radiosonde",
        "title": "Radiosonda",
        "subtitle": "arrancar / parar auto_rx",
        "kind": "toggle_radiosonde",
        "script_start": "/home/ramon/bin/radiosonde-start.sh",
        "script_stop": "/home/ramon/bin/radiosonde-stop.sh",
        "icon": "weather-overcast-symbolic",
        "pat_allowed": True,
        "css": "radiosonde",
        "resources": ["rtlsdr"],
    },
]

CSS = b"""
window {
  background: #111827;
  color: #f3f4f6;
}
label {
  color: #f3f4f6;
}
entry {
  color: #111827;
  background: #f9fafb;
}
button {
  color: #111827;
  background: #e5e7eb;
}
button label,
button image {
  color: #111827;
}
button:hover {
  background: #f3f4f6;
}
.toolbar-btn label,
.toolbar-btn image {
  color: #111827;
}
.web-mini-btn {
  min-height: 30px;
  padding: 3px 12px;
  background: #99f6e4;
  border: 1px solid #2dd4bf;
  border-radius: 999px;
  box-shadow: none;
}
.web-mini-btn:hover {
  background: #5eead4;
  border: 1px solid #14b8a6;
}
.web-mini-btn label,
.web-mini-btn image {
  color: #134e4a;
  font-size: 12px;
  font-weight: 700;
}
textview,
textview text {
  background: #0f172a;
  color: #f3f4f6;
}
headerbar {
  background: #0f172a;
  color: #f3f4f6;
}
.title-main {
  font-size: 22px;
  font-weight: 800;
  color: #f9fafb;
}
.subtitle-main {
  font-size: 12px;
  opacity: 0.92;
  color: #e5e7eb;
}
.section-title {
  font-size: 18px;
  font-weight: 800;
  color: #f9fafb;
}
.card {
  background: #1f2937;
  border-radius: 18px;
  padding: 12px;
}
.card:hover {
  background: #243244;
}
.card.panel {
  background: #1f2937;
}
.card.aprs {
  background: #2563eb;
}
.card.digital {
  background: #7c3aed;
}
.card.wsjt {
  background: #c2410c;
}
.card.radiosonde {
  background: #0369a1;
}
.card.accent {
  background: #1d4ed8;
}
.card.success {
  background: #166534;
}
.card.danger {
  background: #991b1b;
}
.card-title {
  color: white;
  font-size: 15px;
  font-weight: 800;
}
.card-subtitle {
  color: rgba(255,255,255,0.92);
  font-size: 10px;
}
.run-badge {
  color: #dcfce7;
  background: #166534;
  border-radius: 999px;
  padding: 1px 7px;
  font-size: 9px;
  font-weight: 800;
}
.status-ok {
  color: #22c55e;
  font-weight: 800;
}
.status-warn {
  color: #f59e0b;
  font-weight: 800;
}
.status-err {
  color: #ef4444;
  font-weight: 800;
}
.pat-banner {
  border-radius: 16px;
  padding: 12px;
}
.pat-banner.pat-on {
  background: #14532d;
}
.pat-banner.pat-off {
  background: #3f3f46;
}
.pat-banner-title {
  color: white;
  font-size: 24px;
  font-weight: 900;
}
.pat-banner-subtitle {
  color: rgba(255,255,255,0.92);
  font-size: 13px;
}
.mono {
  font-family: monospace;
  color: #f3f4f6;
}
"""


def ensure_dirs() -> None:
    for path in (APP_DIR, BIN_DIR, CONF_DIR, LOG_DIR, ICON_DIR):
        path.mkdir(parents=True, exist_ok=True)


def shell_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def save_env(data: dict[str, str]) -> None:
    lines: list[str] = []
    for key, _label in FIELD_SPECS:
        value = data.get(key, DEFAULT_ENV.get(key, ""))
        lines.append(f'{key}="{shell_escape(value)}"')
    RADIO_ENV.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_default_env() -> None:
    if not RADIO_ENV.exists():
        save_env(DEFAULT_ENV)


def load_env() -> dict[str, str]:
    write_default_env()
    data = DEFAULT_ENV.copy()
    for line in RADIO_ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value.startswith('"') and value.endswith('"') and len(value) >= 2:
            value = value[1:-1]
        data[key] = value
    return data


def write_default_actions() -> None:
    builtins_by_id = {action["id"]: action for action in DEFAULT_ACTIONS}

    if not ACTIONS_JSON.exists():
        ACTIONS_JSON.write_text(json.dumps({"actions": DEFAULT_ACTIONS}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return

    try:
        payload = json.loads(ACTIONS_JSON.read_text(encoding="utf-8"))
    except Exception:
        payload = {"actions": []}

    actions = payload.get("actions", [])
    if not isinstance(actions, list):
        actions = []

    existing_by_id: dict[str, dict[str, Any]] = {}
    custom_actions: list[dict[str, Any]] = []

    for action in actions:
        if not isinstance(action, dict):
            continue
        action_id = action.get("id")
        if not action_id:
            continue
        if action_id in builtins_by_id:
            existing_by_id[action_id] = action
        else:
            custom_actions.append(action)

    merged_actions: list[dict[str, Any]] = []
    for default_action in DEFAULT_ACTIONS:
        action_id = default_action["id"]
        merged = default_action.copy()
        current = existing_by_id.get(action_id)
        if current:
            for key, value in current.items():
                if key == "id":
                    continue
                merged[key] = value
        merged_actions.append(merged)

    merged_actions.extend(custom_actions)
    ACTIONS_JSON.write_text(json.dumps({"actions": merged_actions}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_default_resources() -> None:
    if RESOURCES_JSON.exists():
        return
    RESOURCES_JSON.write_text(json.dumps({"resources": DEFAULT_RESOURCES}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_resources_catalog() -> list[dict[str, str]]:
    write_default_resources()
    try:
        payload = json.loads(RESOURCES_JSON.read_text(encoding="utf-8"))
        resources = payload.get("resources", [])
        if isinstance(resources, list):
            cleaned: list[dict[str, str]] = []
            for item in resources:
                if not isinstance(item, dict):
                    continue
                resource_id = str(item.get("id", "")).strip()
                if not resource_id:
                    continue
                cleaned.append(
                    {
                        "id": resource_id,
                        "title": str(item.get("title", resource_id)).strip() or resource_id,
                        "description": str(item.get("description", "")).strip(),
                    }
                )
            return cleaned
    except Exception:
        pass
    return DEFAULT_RESOURCES.copy()


def save_resources_catalog(resources: list[dict[str, str]]) -> None:
    RESOURCES_JSON.write_text(json.dumps({"resources": resources}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_resource_list(value: str | list[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        items = value
    else:
        items = str(value).split(",")
    seen = set()
    out: list[str] = []
    for item in items:
        token = str(item).strip()
        if not token or token in seen:
            continue
        seen.add(token)
        out.append(token)
    return out


def parse_web_links(value: Any) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    if value is None:
        return links

    if isinstance(value, list):
        for item in value:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title", "")).strip()
            url = str(item.get("url", "")).strip()
            if title and url:
                links.append({"title": title, "url": url})
        return links

    text = str(value)
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if "|" in line:
            title, url = line.split("|", 1)
        else:
            title, url = line, line
        title = title.strip()
        url = url.strip()
        if title and url:
            links.append({"title": title, "url": url})
    return links


def web_links_to_text(links: Any) -> str:
    parsed = parse_web_links(links)
    return "\n".join(f"{item['title']} | {item['url']}" for item in parsed)


def write_default_web_links() -> None:
    if WEBS_JSON.exists():
        return
    WEBS_JSON.write_text(json.dumps({"web_links": []}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_global_web_links() -> list[dict[str, str]]:
    write_default_web_links()
    try:
        payload = json.loads(WEBS_JSON.read_text(encoding="utf-8"))
        return parse_web_links(payload.get("web_links"))
    except Exception:
        return []


def save_global_web_links(links: list[dict[str, str]]) -> None:
    WEBS_JSON.write_text(json.dumps({"web_links": links}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def resource_caption(resources: list[dict[str, str]]) -> str:
    if not resources:
        return "Sin recursos definidos."
    return "\n".join(
        f"• {res['id']} — {res.get('title', res['id'])}" + (f" ({res['description']})" if res.get("description") else "")
        for res in resources
    )


def slugify_title(title: str) -> str:
    normalized = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", normalized.lower()).strip("-")
    return slug or "programa"


def write_executable_script(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def template_start_script(slug: str, title: str, start_command: str) -> str:
    return f"""#!/bin/bash
set -u

PIDFILE="$HOME/radio/run/{slug}.pid"
LOGFILE="$HOME/radio/logs/{slug}.log"
mkdir -p "$HOME/radio/run" "$HOME/radio/logs"

if [ -f "$PIDFILE" ]; then
  PID="$(cat "$PIDFILE")"
  if kill -0 "$PID" 2>/dev/null; then
    echo "{title} ya estaba activo"
    exit 0
  fi
  rm -f "$PIDFILE"
fi

COMMAND=$(cat <<'__RADIO_CMD__'
{start_command}
__RADIO_CMD__
)

nohup bash -lc "$COMMAND" >>"$LOGFILE" 2>&1 &
PID=$!
echo "$PID" > "$PIDFILE"

sleep 2

if kill -0 "$PID" 2>/dev/null; then
  echo "{title} arrancado. PID=$PID"
  exit 0
fi

echo "ERROR: {title} no arrancó"
rm -f "$PIDFILE"
exit 1
"""


def template_stop_script(slug: str, title: str) -> str:
    return f"""#!/bin/bash
set -u

PIDFILE="$HOME/radio/run/{slug}.pid"

if [ -f "$PIDFILE" ]; then
  PID="$(cat "$PIDFILE")"
  if kill -0 "$PID" 2>/dev/null; then
    kill "$PID" 2>/dev/null || true
    sleep 2
    if kill -0 "$PID" 2>/dev/null; then
      kill -9 "$PID" 2>/dev/null || true
    fi
  fi
  rm -f "$PIDFILE"
fi

if "$HOME/radio/bin/{slug}-status.sh" >/dev/null 2>&1; then
  echo "ERROR: {title} sigue activo"
  exit 1
fi

echo "{title} parado"
exit 0
"""


def template_status_script(slug: str, title: str) -> str:
    return f"""#!/bin/bash
set -u

PIDFILE="$HOME/radio/run/{slug}.pid"

if [ -f "$PIDFILE" ]; then
  PID="$(cat "$PIDFILE")"
  if kill -0 "$PID" 2>/dev/null; then
    echo "activo"
    exit 0
  fi
  rm -f "$PIDFILE"
fi

echo "parado"
exit 1
"""


def load_actions() -> list[dict[str, Any]]:
    write_default_actions()
    try:
        payload = json.loads(ACTIONS_JSON.read_text(encoding="utf-8"))
        actions = payload.get("actions", [])
        if isinstance(actions, list):
            filtered: list[dict[str, Any]] = []
            for action in actions:
                if not isinstance(action, dict):
                    continue
                if action.get("id") in {"config", "stop", "config_top", "stop_top"}:
                    continue
                filtered.append(action)
            return filtered
    except Exception:
        pass
    return DEFAULT_ACTIONS


def run_generate_configs() -> None:
    script = BIN_DIR / "radio-generate-configs.sh"
    if script.exists():
        subprocess.run([str(script)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)


def pat_active() -> bool:
    status_script = BIN_DIR / "radio-pat-status.sh"
    if status_script.exists():
        proc = subprocess.run([str(status_script)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return proc.returncode == 0
    return False


def radiosonde_active() -> bool:
    checks = [
        "docker inspect -f '{{.State.Running}}' radiosonde_auto_rx 2>/dev/null | grep -Fxq true",
        "pgrep -af '[a]uto_rx.py' >/dev/null",
    ]
    for cmd in checks:
        proc = subprocess.run(
            ["bash", "-lc", cmd],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if proc.returncode == 0:
            return True
    return False


def toggle_status_active(status_script: str | None) -> bool:
    if not status_script:
        return False
    path = Path(status_script).expanduser()
    if not path.exists():
        return False
    proc = subprocess.run(
        [str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return proc.returncode == 0


def derived_status_script(script_path: str | None) -> str | None:
    if not script_path:
        return None
    path = Path(script_path).expanduser()
    name = path.name

    candidates = []
    if name.endswith("-start.sh"):
        candidates.append(path.with_name(name[:-9] + "-status.sh"))
    if name.endswith(".sh"):
        stem = name[:-3]
        candidates.append(path.with_name(stem + "-status.sh"))
    if name.startswith("radio-") and name.endswith(".sh"):
        stem = name[:-3]
        candidates.append(path.with_name(stem + "-status.sh"))

    seen = set()
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        if candidate.exists():
            return str(candidate)
    return None


def aprs_active() -> bool:
    checks = [
        "pgrep -af '[d]irewolf' >/dev/null",
        "pgrep -af 'YAAC\.jar' >/dev/null",
    ]
    matches = 0
    for cmd in checks:
        proc = subprocess.run(
            ["bash", "-lc", cmd],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if proc.returncode == 0:
            matches += 1
    return matches >= 1


def digital_active() -> bool:
    checks = [
        "pgrep -af '[f]ldigi' >/dev/null",
        "pgrep -af '[f]lrig' >/dev/null",
    ]
    matches = 0
    for cmd in checks:
        proc = subprocess.run(
            ["bash", "-lc", cmd],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if proc.returncode == 0:
            matches += 1
    return matches >= 1


def wsjt_active() -> bool:
    proc = subprocess.run(
        ["bash", "-lc", "pgrep -af '[w]sjtx' >/dev/null"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return proc.returncode == 0


class ActionButton(Gtk.Button):
    def __init__(self, action: dict[str, Any], callback):
        super().__init__()
        self.action = action
        self.set_hexpand(True)
        self.add_css_class("flat")
        self.add_css_class("card")
        self.add_css_class(action.get("css", "panel"))
        self.set_size_request(170, 58)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        box.set_margin_top(2)
        box.set_margin_bottom(2)
        box.set_margin_start(2)
        box.set_margin_end(2)

        top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        icon = self._build_icon_widget(action)
        icon.set_halign(Gtk.Align.START)
        top_row.append(icon)

        self.run_badge = Gtk.Label(label="● RUN")
        self.run_badge.add_css_class("run-badge")
        self.run_badge.set_halign(Gtk.Align.END)
        self.run_badge.set_hexpand(True)
        self.run_badge.set_visible(False)
        top_row.append(self.run_badge)

        title = Gtk.Label(label=action.get("title", action.get("id", "Acción")))
        title.set_halign(Gtk.Align.START)
        title.set_xalign(0.0)
        title.set_wrap(True)
        title.add_css_class("card-title")

        subtitle = Gtk.Label(label=action.get("subtitle", ""))
        subtitle.set_halign(Gtk.Align.START)
        subtitle.set_xalign(0.0)
        subtitle.set_wrap(True)
        subtitle.add_css_class("card-subtitle")

        box.append(top_row)
        box.append(title)
        if action.get("subtitle"):
            box.append(subtitle)
        self.set_child(box)
        self.connect("clicked", lambda _btn: callback(self.action))

    def set_running(self, active: bool) -> None:
        self.run_badge.set_visible(bool(active))

    def _build_icon_widget(self, action: dict[str, Any]) -> Gtk.Widget:
        icon_path = action.get("icon_path")
        if icon_path:
            path = Path(icon_path).expanduser()
            if path.exists():
                picture = Gtk.Picture.new_for_filename(str(path))
                picture.set_content_fit(Gtk.ContentFit.CONTAIN)
                picture.set_size_request(14, 14)
                picture.set_can_shrink(True)
                return picture

        image = Gtk.Image.new_from_icon_name(action.get("icon", "applications-system-symbolic"))
        image.set_pixel_size(14)
        return image


class ConfigRow(Gtk.Box):
    def __init__(self, label_text: str, value: str):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        label = Gtk.Label(label=label_text)
        label.set_size_request(180, -1)
        label.set_halign(Gtk.Align.START)
        label.set_xalign(0.0)

        self.entry = Gtk.Entry()
        self.entry.set_hexpand(True)
        self.entry.set_text(value)

        self.append(label)
        self.append(self.entry)


class RadioPanelWindow(Gtk.ApplicationWindow):
    def __init__(self, app: Gtk.Application):
        super().__init__(application=app)
        self.set_title("Panel de radio")
        self.set_default_size(1080, 760)

        self.env_data = load_env()
        self.actions = load_actions()
        self.processes: dict[str, subprocess.Popen[str]] = {}
        self.action_buttons: list[ActionButton] = []

        self._install_css()
        self._build_ui()
        self._refresh_status()
        GLib.timeout_add_seconds(2, self._poll_state)

    def _install_css(self) -> None:
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        display = Gdk.Display.get_default()
        if display:
            Gtk.StyleContext.add_provider_for_display(display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def _make_text_icon_button(self, label_text: str, icon_name: str) -> Gtk.Button:
        button = Gtk.Button()
        button.add_css_class("toolbar-btn")
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        icon = Gtk.Image.new_from_icon_name(icon_name)
        icon.set_pixel_size(16)
        label = Gtk.Label(label=label_text)
        box.append(icon)
        box.append(label)
        button.set_child(box)
        return button

    def _on_stack_page_changed(self, _stack, _pspec) -> None:
        if not hasattr(self, "bottom_status"):
            return
        self.bottom_status.set_visible(self.stack.get_visible_child_name() == "panel")

    def _make_web_button(self, title: str, url: str) -> Gtk.Button:
        button = Gtk.Button(label=title)
        button.add_css_class("web-mini-btn")
        button.connect("clicked", lambda _btn: self._open_web_link(title, url))
        return button

    def _open_web_link(self, title: str, url: str) -> None:
        subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self._append_log(f"Abierta web '{title}': {url}")
        self._set_runtime_state("Web abierta", title, "ok")

    def _on_edit_global_webs(self, _button) -> None:
        current_links = load_global_web_links()

        dialog = Gtk.Dialog(transient_for=self, modal=True, title="Webs rápidas")
        dialog.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        dialog.add_button("Guardar", Gtk.ResponseType.OK)
        content = dialog.get_content_area()
        content.set_spacing(10)

        form = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        form.set_margin_top(12)
        form.set_margin_bottom(12)
        form.set_margin_start(12)
        form.set_margin_end(12)

        info = Gtk.Label(label="Una línea por botón con formato: Título | URL")
        info.set_wrap(True)
        info.set_xalign(0.0)

        webs_text = Gtk.TextView()
        webs_text.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        webs_text.set_monospace(True)
        buf = webs_text.get_buffer()
        buf.set_text(web_links_to_text(current_links))

        webs_scroll = Gtk.ScrolledWindow()
        webs_scroll.set_min_content_height(180)
        webs_scroll.set_child(webs_text)

        form.append(info)
        form.append(webs_scroll)
        content.append(form)

        def on_response(dlg, response):
            if response != Gtk.ResponseType.OK:
                dlg.close()
                return
            buf = webs_text.get_buffer()
            value = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True)
            links = parse_web_links(value)
            save_global_web_links(links)
            self._append_log("Webs rápidas actualizadas")
            self._set_runtime_state("Webs actualizadas", f"{len(links)} botones web guardados.", "ok")
            self._rebuild_panel_page()
            dlg.close()

        dialog.connect("response", on_response)
        dialog.show()

    def _rebuild_panel_page(self) -> None:
        self.actions = load_actions()
        old_page = self.stack.get_child_by_name("panel")
        self.action_buttons = []
        new_page = self._build_panel_page()
        self.stack.add_titled(new_page, "panel", "Panel")
        if old_page is not None:
            self.stack.remove(old_page)
        self.stack.set_visible_child_name("panel")

    def _action_is_active(self, action: dict[str, Any]) -> bool:
        action_id = action.get("id")
        kind = action.get("kind")

        if action_id == "aprs":
            return aprs_active()
        if action_id == "digital":
            return digital_active()
        if action_id == "wsjt":
            return wsjt_active()

        if kind == "toggle_pat":
            return pat_active()
        if kind == "toggle_radiosonde":
            return radiosonde_active()
        if kind == "toggle":
            return toggle_status_active(action.get("script_status"))

        status_script = action.get("script_status") or derived_status_script(action.get("script"))
        if status_script:
            return toggle_status_active(status_script)

        return False

    def _refresh_button_run_states(self) -> None:
        for button in self.action_buttons:
            try:
                button.set_running(self._action_is_active(button.action))
            except Exception:
                pass

    def _action_resources(self, action: dict[str, Any]) -> list[str]:
        return parse_resource_list(action.get("resources"))

    def _occupied_resources(self) -> dict[str, list[str]]:
        occupied: dict[str, list[str]] = {}
        for button in self.action_buttons:
            action = button.action
            if not self._action_is_active(action):
                continue
            for resource in self._action_resources(action):
                occupied.setdefault(resource, []).append(action.get("title", action.get("id", resource)))
        return occupied

    def _conflicting_resources(self, action: dict[str, Any], occupied: dict[str, list[str]]) -> list[str]:
        if self._action_is_active(action):
            return []
        conflicts: list[str] = []
        for resource in self._action_resources(action):
            if resource in occupied:
                conflicts.append(resource)
        return conflicts

    def _refresh_resources_summary(self) -> None:
        if hasattr(self, "resources_summary"):
            self.resources_summary.set_label(resource_caption(load_resources_catalog()))

    def _save_actions_payload(self, actions: list[dict[str, Any]]) -> None:
        ACTIONS_JSON.write_text(json.dumps({"actions": actions}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        write_default_actions()

    def _on_add_resource(self, _button) -> None:
        dialog = Gtk.Dialog(transient_for=self, modal=True, title="Añadir recurso")
        dialog.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        dialog.add_button("Guardar", Gtk.ResponseType.OK)
        content = dialog.get_content_area()
        content.set_spacing(10)

        form = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        form.set_margin_top(12)
        form.set_margin_bottom(12)
        form.set_margin_start(12)
        form.set_margin_end(12)

        title_row = ConfigRow("Nombre", "")
        id_row = ConfigRow("ID (opcional)", "")
        desc_row = ConfigRow("Descripción", "")

        for widget in (title_row, id_row, desc_row):
            form.append(widget)
        content.append(form)

        def on_response(dlg, response):
            if response != Gtk.ResponseType.OK:
                dlg.close()
                return

            title = title_row.entry.get_text().strip()
            resource_id = id_row.entry.get_text().strip()
            description = desc_row.entry.get_text().strip()

            if not title and not resource_id:
                self._show_message("Falta el recurso", "Debes indicar al menos un nombre o un ID.", Gtk.MessageType.ERROR)
                return

            if not resource_id:
                resource_id = slugify_title(title)

            resources = load_resources_catalog()
            if any(r["id"] == resource_id for r in resources):
                self._show_message("Ya existe", f"Ya existe el recurso {resource_id}.", Gtk.MessageType.ERROR)
                return

            resources.append({"id": resource_id, "title": title or resource_id, "description": description})
            save_resources_catalog(resources)
            self._refresh_resources_summary()
            self._append_log(f"Recurso añadido: {resource_id}")
            self._set_runtime_state("Recurso añadido", f"Se añadió {resource_id}.", "ok")
            dlg.close()

        dialog.connect("response", on_response)
        dialog.show()

    def _on_delete_resource(self, _button) -> None:
        resources = load_resources_catalog()
        if not resources:
            self._show_message("No hay recursos", "No hay recursos definidos para eliminar.")
            return

        dialog = Gtk.Dialog(transient_for=self, modal=True, title="Eliminar recurso")
        dialog.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        dialog.add_button("Eliminar", Gtk.ResponseType.OK)
        content = dialog.get_content_area()
        content.set_spacing(10)

        form = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        form.set_margin_top(12)
        form.set_margin_bottom(12)
        form.set_margin_start(12)
        form.set_margin_end(12)

        combo_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        combo_label = Gtk.Label(label="Recurso")
        combo_label.set_size_request(180, -1)
        combo_label.set_halign(Gtk.Align.START)
        combo_label.set_xalign(0.0)
        combo = Gtk.ComboBoxText()
        for resource in resources:
            combo.append(resource["id"], f"{resource['id']} — {resource.get('title', resource['id'])}")
        combo.set_active(0)
        combo_box.append(combo_label)
        combo_box.append(combo)

        clean_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        clean_label = Gtk.Label(label="Quitar de programas")
        clean_label.set_size_request(180, -1)
        clean_label.set_halign(Gtk.Align.START)
        clean_label.set_xalign(0.0)
        clean_check = Gtk.CheckButton()
        clean_check.set_active(True)
        clean_box.append(clean_label)
        clean_box.append(clean_check)

        for widget in (combo_box, clean_box):
            form.append(widget)
        content.append(form)

        def on_response(dlg, response):
            if response != Gtk.ResponseType.OK:
                dlg.close()
                return

            resource_id = combo.get_active_id()
            if not resource_id:
                return

            remaining = [r for r in resources if r["id"] != resource_id]
            save_resources_catalog(remaining)

            if clean_check.get_active() and ACTIONS_JSON.exists():
                try:
                    payload = json.loads(ACTIONS_JSON.read_text(encoding="utf-8"))
                    actions = payload.get("actions", [])
                    if isinstance(actions, list):
                        changed = False
                        for action in actions:
                            if not isinstance(action, dict):
                                continue
                            parsed = parse_resource_list(action.get("resources"))
                            if resource_id in parsed:
                                action["resources"] = [r for r in parsed if r != resource_id]
                                changed = True
                        if changed:
                            self._save_actions_payload(actions)
                except Exception:
                    pass

            self._refresh_resources_summary()
            self._append_log(f"Recurso eliminado: {resource_id}")
            self._set_runtime_state("Recurso eliminado", f"Se eliminó {resource_id}.", "ok")
            dlg.close()

        dialog.connect("response", on_response)
        dialog.show()


    def _save_custom_action(self, action: dict[str, Any]) -> None:
        payload = {"actions": []}
        if ACTIONS_JSON.exists():
            try:
                payload = json.loads(ACTIONS_JSON.read_text(encoding="utf-8"))
            except Exception:
                payload = {"actions": []}
        actions = payload.get("actions", [])
        if not isinstance(actions, list):
            actions = []

        existing_index = None
        for i, item in enumerate(actions):
            if isinstance(item, dict) and item.get("id") == action.get("id"):
                existing_index = i
                break

        if existing_index is None:
            actions.append(action)
        else:
            actions[existing_index] = action

        payload["actions"] = actions
        ACTIONS_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def _load_custom_actions(self) -> list[dict[str, Any]]:
        write_default_actions()
        if not ACTIONS_JSON.exists():
            return []
        try:
            payload = json.loads(ACTIONS_JSON.read_text(encoding="utf-8"))
        except Exception:
            return []
        actions = payload.get("actions", [])
        if not isinstance(actions, list):
            return []
        builtins = {action["id"] for action in DEFAULT_ACTIONS}
        custom: list[dict[str, Any]] = []
        for action in actions:
            if not isinstance(action, dict):
                continue
            action_id = action.get("id")
            if action_id in builtins or action_id in {"config", "stop", "config_top", "stop_top"}:
                continue
            custom.append(action)
        return custom

    def _load_all_managed_actions(self) -> list[dict[str, Any]]:
        write_default_actions()
        if not ACTIONS_JSON.exists():
            return []
        try:
            payload = json.loads(ACTIONS_JSON.read_text(encoding="utf-8"))
        except Exception:
            return []
        actions = payload.get("actions", [])
        if not isinstance(actions, list):
            return []
        filtered: list[dict[str, Any]] = []
        for action in actions:
            if not isinstance(action, dict):
                continue
            if action.get("id") in {"config", "stop", "config_top", "stop_top"}:
                continue
            filtered.append(action)
        return filtered

    def _remove_custom_action(self, action_id: str) -> dict[str, Any] | None:
        if not ACTIONS_JSON.exists():
            return None
        try:
            payload = json.loads(ACTIONS_JSON.read_text(encoding="utf-8"))
        except Exception:
            return None
        actions = payload.get("actions", [])
        if not isinstance(actions, list):
            return None

        removed = None
        remaining = []
        for action in actions:
            if isinstance(action, dict) and action.get("id") == action_id and removed is None:
                removed = action
                continue
            remaining.append(action)

        if removed is None:
            return None

        payload["actions"] = remaining
        ACTIONS_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return removed

    def _delete_program_files(self, action: dict[str, Any]) -> list[str]:
        removed_paths: list[str] = []
        for key in ("script", "script_start", "script_stop", "script_status"):
            value = action.get(key)
            if not isinstance(value, str) or not value.strip():
                continue
            path = Path(value).expanduser()
            try:
                resolved = path.resolve()
                bin_resolved = BIN_DIR.resolve()
                if not resolved.is_relative_to(bin_resolved):
                    continue
            except Exception:
                continue
            if path.exists():
                try:
                    path.unlink()
                    removed_paths.append(str(path))
                except Exception:
                    pass
        return removed_paths

    def _create_program_templates(self, title: str, start_command: str) -> tuple[str, str, str, str]:
        slug = slugify_title(title)
        start_path = BIN_DIR / f"{slug}-start.sh"
        stop_path = BIN_DIR / f"{slug}-stop.sh"
        status_path = BIN_DIR / f"{slug}-status.sh"

        for path in (start_path, stop_path, status_path):
            if path.exists():
                raise FileExistsError(f"Ya existe: {path}")

        write_executable_script(start_path, template_start_script(slug, title, start_command))
        write_executable_script(stop_path, template_stop_script(slug, title))
        write_executable_script(status_path, template_status_script(slug, title))
        return slug, str(start_path), str(stop_path), str(status_path)

    def _on_add_program(self, _button) -> None:
        dialog = Gtk.Dialog(transient_for=self, modal=True, title="Añadir programa")
        dialog.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        dialog.add_button("Guardar", Gtk.ResponseType.OK)
        content = dialog.get_content_area()
        content.set_spacing(10)

        form = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        form.set_margin_top(12)
        form.set_margin_bottom(12)
        form.set_margin_start(12)
        form.set_margin_end(12)

        title_row = ConfigRow("Título", "")
        subtitle_row = ConfigRow("Subtítulo", "")
        command_row = ConfigRow("Comando de arranque", "")

        resources_catalog = load_resources_catalog()
        resources_label = Gtk.Label(label="Recursos usados")
        resources_label.set_size_request(180, -1)
        resources_label.set_halign(Gtk.Align.START)
        resources_label.set_xalign(0.0)

        resources_checks_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        resources_checks: dict[str, Gtk.CheckButton] = {}
        if resources_catalog:
            for resource in resources_catalog:
                check = Gtk.CheckButton(label=f"{resource['id']} — {resource.get('title', resource['id'])}")
                if resource.get("description"):
                    check.set_tooltip_text(resource["description"])
                resources_checks[resource["id"]] = check
                resources_checks_box.append(check)
        else:
            no_res = Gtk.Label(label="No hay recursos definidos.")
            no_res.set_halign(Gtk.Align.START)
            no_res.set_xalign(0.0)
            resources_checks_box.append(no_res)

        resources_row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        resources_row_box.append(resources_label)
        resources_row_box.append(resources_checks_box)

        type_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        type_label = Gtk.Label(label="Tipo")
        type_label.set_size_request(180, -1)
        type_label.set_halign(Gtk.Align.START)
        type_label.set_xalign(0.0)
        type_combo = Gtk.ComboBoxText()
        type_combo.append("script", "Programa normal")
        type_combo.append("toggle", "Conmutado arranque/parada")
        type_combo.set_active_id("script")
        type_box.append(type_label)
        type_box.append(type_combo)

        icon_row = ConfigRow("Icono", "applications-system-symbolic")

        color_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        color_label = Gtk.Label(label="Color")
        color_label.set_size_request(180, -1)
        color_label.set_halign(Gtk.Align.START)
        color_label.set_xalign(0.0)
        color_combo = Gtk.ComboBoxText()
        for color_id, caption in [
            ("panel", "Gris"),
            ("aprs", "Azul APRS"),
            ("digital", "Violeta Digital"),
            ("wsjt", "Naranja WSJT-X"),
            ("radiosonde", "Azul Radiosonda"),
            ("success", "Verde"),
            ("danger", "Rojo"),
            ("accent", "Turquesa"),
        ]:
            color_combo.append(color_id, caption)
        color_combo.set_active_id("panel")
        color_box.append(color_label)
        color_box.append(color_combo)

        pat_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        pat_label = Gtk.Label(label="Permitir con PAT activo")
        pat_label.set_size_request(180, -1)
        pat_label.set_halign(Gtk.Align.START)
        pat_label.set_xalign(0.0)
        pat_check = Gtk.CheckButton()
        pat_check.set_active(True)
        pat_box.append(pat_label)
        pat_box.append(pat_check)

        hint = Gtk.Label(label="Al guardar se crearán automáticamente start/stop/status en ~/radio/bin. El script de arranque usará el comando que escribas y stop/status funcionarán con PID file.")
        hint.set_wrap(True)
        hint.set_xalign(0.0)

        for widget in (title_row, subtitle_row, command_row, resources_row_box, type_box, icon_row, color_box, pat_box, hint):
            form.append(widget)

        content.append(form)

        def on_response(dlg, response):
            if response != Gtk.ResponseType.OK:
                dlg.close()
                return

            title = title_row.entry.get_text().strip()
            subtitle = subtitle_row.entry.get_text().strip()
            start_command = command_row.entry.get_text().strip()
            selected_resources = [resource_id for resource_id, check in resources_checks.items() if check.get_active()]
            kind = type_combo.get_active_id() or "script"
            icon_name = icon_row.entry.get_text().strip() or "applications-system-symbolic"
            color_id = color_combo.get_active_id() or "panel"
            pat_allowed = pat_check.get_active()

            if not title:
                self._show_message("Falta el título", "Debes indicar un título para el programa.", Gtk.MessageType.ERROR)
                return

            if not start_command:
                self._show_message("Falta el comando", "Debes indicar el comando de arranque.", Gtk.MessageType.ERROR)
                return

            try:
                slug, start_script, stop_script, status_script = self._create_program_templates(title, start_command)
                action = {
                    "id": slug.replace("-", "_"),
                    "title": title,
                    "subtitle": subtitle,
                    "icon": icon_name,
                    "css": color_id,
                    "pat_allowed": pat_allowed,
                    "resources": selected_resources,
                }
                if kind == "toggle":
                    action["kind"] = "toggle"
                    action["script_start"] = start_script
                    action["script_stop"] = stop_script
                    action["script_status"] = status_script
                    if not subtitle:
                        action["subtitle"] = "arrancar / parar"
                else:
                    action["kind"] = "script"
                    action["script"] = start_script
                    if not subtitle:
                        action["subtitle"] = "script de arranque"

                self._save_custom_action(action)
                self._append_log(f"Programa añadido: {title}")
                self._append_log(f"Plantillas creadas: {start_script}, {stop_script}, {status_script}")
                self._set_runtime_state("Programa añadido", f"Se creó {title} y sus plantillas.", "ok")
                self._rebuild_panel_page()
                dlg.close()
                self._show_message(
                    "Programa añadido",
                    f"Se han creado:\n{start_script}\n{stop_script}\n{status_script}\n\nEl comando de arranque ya quedó integrado en start.sh. Stop/status usan PID file."
                )
            except FileExistsError as exc:
                self._show_message("Ya existe", str(exc), Gtk.MessageType.ERROR)
            except Exception as exc:
                self._show_message("Error al añadir programa", str(exc), Gtk.MessageType.ERROR)

        dialog.connect("response", on_response)
        dialog.show()


    def _on_edit_program_resources(self, _button) -> None:
        actions = self._load_all_managed_actions()
        if not actions:
            self._show_message("No hay programas", "No hay programas gestionados para editar.")
            return

        resources = load_resources_catalog()
        dialog = Gtk.Dialog(transient_for=self, modal=True, title="Editar recursos de programa")
        dialog.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        dialog.add_button("Guardar", Gtk.ResponseType.OK)
        content = dialog.get_content_area()
        content.set_spacing(10)

        form = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        form.set_margin_top(12)
        form.set_margin_bottom(12)
        form.set_margin_start(12)
        form.set_margin_end(12)

        prog_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        prog_label = Gtk.Label(label="Programa")
        prog_label.set_size_request(180, -1)
        prog_label.set_halign(Gtk.Align.START)
        prog_label.set_xalign(0.0)
        prog_combo = Gtk.ComboBoxText()
        for action in actions:
            prog_combo.append(action.get("id", ""), action.get("title", action.get("id", "Programa")))
        prog_combo.set_active(0)
        prog_box.append(prog_label)
        prog_box.append(prog_combo)

        resources_label = Gtk.Label(label="Recursos")
        resources_label.set_size_request(180, -1)
        resources_label.set_halign(Gtk.Align.START)
        resources_label.set_xalign(0.0)

        resources_checks_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        resources_checks: dict[str, Gtk.CheckButton] = {}
        if resources:
            for resource in resources:
                check = Gtk.CheckButton(label=f"{resource['id']} — {resource.get('title', resource['id'])}")
                if resource.get("description"):
                    check.set_tooltip_text(resource["description"])
                resources_checks[resource["id"]] = check
                resources_checks_box.append(check)
        else:
            no_res = Gtk.Label(label="No hay recursos definidos.")
            no_res.set_halign(Gtk.Align.START)
            no_res.set_xalign(0.0)
            resources_checks_box.append(no_res)

        resources_row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        resources_row_box.append(resources_label)
        resources_row_box.append(resources_checks_box)

        form.append(prog_box)
        form.append(resources_row_box)
        content.append(form)

        actions_by_id = {action.get("id", ""): action for action in actions}

        def load_selected_resources() -> None:
            action_id = prog_combo.get_active_id()
            current = actions_by_id.get(action_id or "", {})
            current_resources = set(parse_resource_list(current.get("resources")))
            for resource_id, check in resources_checks.items():
                check.set_active(resource_id in current_resources)

        prog_combo.connect("changed", lambda _combo: load_selected_resources())
        load_selected_resources()

        def on_response(dlg, response):
            if response != Gtk.ResponseType.OK:
                dlg.close()
                return

            action_id = prog_combo.get_active_id()
            if not action_id:
                self._show_message("Falta selección", "Debes elegir un programa.", Gtk.MessageType.ERROR)
                return

            updated_resources = [resource_id for resource_id, check in resources_checks.items() if check.get_active()]
            payload_actions = self._load_all_managed_actions()
            changed = False
            for action in payload_actions:
                if action.get("id") == action_id:
                    action["resources"] = updated_resources
                    changed = True
                    break

            if not changed:
                self._show_message("No encontrado", "No se encontró el programa seleccionado.", Gtk.MessageType.ERROR)
                return

            self._save_actions_payload(payload_actions)
            self._append_log(f"Recursos actualizados para {action_id}: {', '.join(updated_resources) if updated_resources else '(sin recursos)'}")
            self._set_runtime_state("Recursos actualizados", f"Se actualizaron los recursos de {action_id}.", "ok")
            self._rebuild_panel_page()
            self._refresh_resources_summary()
            dlg.close()

        dialog.connect("response", on_response)
        dialog.show()

    def _on_delete_program(self, _button) -> None:
        custom_actions = self._load_custom_actions()
        if not custom_actions:
            self._show_message("No hay programas", "No hay programas añadidos por el usuario para eliminar.")
            return

        dialog = Gtk.Dialog(transient_for=self, modal=True, title="Eliminar programa")
        dialog.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        dialog.add_button("Eliminar", Gtk.ResponseType.OK)
        content = dialog.get_content_area()
        content.set_spacing(10)

        form = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        form.set_margin_top(12)
        form.set_margin_bottom(12)
        form.set_margin_start(12)
        form.set_margin_end(12)

        prog_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        prog_label = Gtk.Label(label="Programa")
        prog_label.set_size_request(180, -1)
        prog_label.set_halign(Gtk.Align.START)
        prog_label.set_xalign(0.0)
        prog_combo = Gtk.ComboBoxText()
        for action in custom_actions:
            prog_combo.append(action.get("id", ""), action.get("title", action.get("id", "Programa")))
        if custom_actions:
            prog_combo.set_active(0)
        prog_box.append(prog_label)
        prog_box.append(prog_combo)

        files_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        files_label = Gtk.Label(label="Eliminar scripts creados")
        files_label.set_size_request(180, -1)
        files_label.set_halign(Gtk.Align.START)
        files_label.set_xalign(0.0)
        files_check = Gtk.CheckButton()
        files_check.set_active(True)
        files_box.append(files_label)
        files_box.append(files_check)

        hint = Gtk.Label(label="Solo se eliminarán automáticamente scripts ubicados dentro de ~/radio/bin.")
        hint.set_wrap(True)
        hint.set_xalign(0.0)

        for widget in (prog_box, files_box, hint):
            form.append(widget)

        content.append(form)

        custom_by_id = {action.get("id"): action for action in custom_actions}

        def on_response(dlg, response):
            if response != Gtk.ResponseType.OK:
                dlg.close()
                return

            action_id = prog_combo.get_active_id()
            if not action_id:
                self._show_message("Falta selección", "Debes elegir un programa para eliminar.", Gtk.MessageType.ERROR)
                return

            action = custom_by_id.get(action_id)
            if not action:
                self._show_message("No encontrado", "No se encontró el programa seleccionado.", Gtk.MessageType.ERROR)
                return

            removed = self._remove_custom_action(action_id)
            if removed is None:
                self._show_message("No eliminado", "No se pudo eliminar el programa de actions.json.", Gtk.MessageType.ERROR)
                return

            removed_files: list[str] = []
            if files_check.get_active():
                removed_files = self._delete_program_files(removed)

            self._append_log(f"Programa eliminado: {removed.get('title', action_id)}")
            if removed_files:
                self._append_log("Scripts eliminados: " + ", ".join(removed_files))
            self._set_runtime_state("Programa eliminado", f"Se eliminó {removed.get('title', action_id)}.", "ok")
            self._rebuild_panel_page()
            dlg.close()

            detail = f"Se eliminó {removed.get('title', action_id)} del panel."
            if removed_files:
                detail += "\n\nScripts eliminados:\n" + "\n".join(removed_files)
            self._show_message("Programa eliminado", detail)

        dialog.connect("response", on_response)
        dialog.show()

    def _build_ui(self) -> None:
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(root)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_hexpand(True)
        self.stack.set_vexpand(True)
        root.append(self.stack)

        self.stack.add_titled(self._build_panel_page(), "panel", "Panel")
        self.stack.add_titled(self._build_config_page(), "config", "Configuración")

        self.bottom_status = self._build_bottom_status()
        root.append(self.bottom_status)
        self.stack.connect("notify::visible-child-name", self._on_stack_page_changed)

    def _build_panel_page(self) -> Gtk.Widget:
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        outer.set_margin_top(24)
        outer.set_margin_bottom(16)
        outer.set_margin_start(24)
        outer.set_margin_end(24)

        info_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        info_card.add_css_class("card")
        info_card.add_css_class("panel")

        row1 = Gtk.Label(label="Operación")
        row1.add_css_class("section-title")
        row1.set_xalign(0.0)
        info_card.append(row1)

        self.station_label = Gtk.Label(label="")
        self.station_label.set_xalign(0.0)
        self.station_label.set_wrap(True)
        info_card.append(self.station_label)

        top_actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        top_actions.set_halign(Gtk.Align.END)

        cfg_action = {
            "id": "config_top",
            "title": "Configurar",
            "subtitle": "",
            "kind": "page",
            "target": "config",
            "icon": "preferences-system-symbolic",
            "pat_allowed": True,
            "css": "accent",
        }
        stop_action = {
            "id": "stop_top",
            "title": "Parar todo",
            "subtitle": "",
            "kind": "script",
            "script": str(BIN_DIR / "radio-stop.sh"),
            "icon": "media-playback-stop-symbolic",
            "pat_allowed": True,
            "css": "danger",
        }

        cfg_btn = ActionButton(cfg_action, self._on_action)
        stop_btn = ActionButton(stop_action, self._on_action)
        self.action_buttons.append(cfg_btn)
        self.action_buttons.append(stop_btn)

        top_actions.append(cfg_btn)
        top_actions.append(stop_btn)
        info_card.append(top_actions)
        outer.append(info_card)

        flow = Gtk.FlowBox()
        flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_max_children_per_line(5)
        flow.set_min_children_per_line(3)
        flow.set_row_spacing(8)
        flow.set_column_spacing(8)
        flow.set_hexpand(True)
        flow.set_vexpand(True)

        for action in self.actions:
            button = ActionButton(action, self._on_action)
            self.action_buttons.append(button)
            flow.insert(button, -1)

        outer.append(flow)

        global_webs = load_global_web_links()
        if global_webs:
            webs_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            webs_card.add_css_class("card")
            webs_card.add_css_class("panel")

            webs_title = Gtk.Label(label="Webs rápidas")
            webs_title.add_css_class("section-title")
            webs_title.set_xalign(0.0)
            webs_card.append(webs_title)

            webs_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            webs_row.set_halign(Gtk.Align.CENTER)
            for link in global_webs:
                webs_row.append(self._make_web_button(link["title"], link["url"]))
            webs_card.append(webs_row)
            outer.append(webs_card)

        return outer

    def _build_config_page(self) -> Gtk.Widget:
        scroller = Gtk.ScrolledWindow()
        scroller.set_hexpand(True)
        scroller.set_vexpand(True)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        box.set_margin_top(24)
        box.set_margin_bottom(24)
        box.set_margin_start(24)
        box.set_margin_end(24)
        scroller.set_child(box)

        title = Gtk.Label(label="Configuración común de la estación")
        title.add_css_class("section-title")
        title.set_xalign(0.0)
        box.append(title)

        desc = Gtk.Label(label="La configuración se guarda en radio.env. Los scripts existentes seguirán usándolo por debajo.")
        desc.set_xalign(0.0)
        desc.set_wrap(True)
        desc.set_css_classes(["card-subtitle"])
        box.append(desc)

        resources_title = Gtk.Label(label="Recursos definidos")
        resources_title.add_css_class("section-title")
        resources_title.set_xalign(0.0)
        box.append(resources_title)

        self.resources_summary = Gtk.Label(label="")
        self.resources_summary.set_xalign(0.0)
        self.resources_summary.set_wrap(True)
        box.append(self.resources_summary)
        self._refresh_resources_summary()

        resources_buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        add_res_btn = self._make_text_icon_button("Añadir recurso", "list-add-symbolic")
        add_res_btn.connect("clicked", self._on_add_resource)
        del_res_btn = self._make_text_icon_button("Eliminar recurso", "user-trash-symbolic")
        del_res_btn.connect("clicked", self._on_delete_resource)
        resources_buttons.append(add_res_btn)
        resources_buttons.append(del_res_btn)
        box.append(resources_buttons)

        self.config_rows: dict[str, ConfigRow] = {}
        for key, label in FIELD_SPECS:
            row = ConfigRow(label, self.env_data.get(key, DEFAULT_ENV.get(key, "")))
            self.config_rows[key] = row
            box.append(row)

        buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)

        back_btn = self._make_text_icon_button("Volver al panel", "go-previous-symbolic")
        back_btn.connect("clicked", lambda _btn: self.stack.set_visible_child_name("panel"))

        save_btn = self._make_text_icon_button("Guardar configuración", "document-save-symbolic")
        save_btn.connect("clicked", self._on_save_config)

        reload_btn = self._make_text_icon_button("Recargar", "view-refresh-symbolic")
        reload_btn.connect("clicked", self._on_reload_config)

        add_btn = self._make_text_icon_button("Añadir programa", "list-add-symbolic")
        add_btn.connect("clicked", self._on_add_program)

        webs_btn = self._make_text_icon_button("Webs rápidas", "applications-internet-symbolic")
        webs_btn.connect("clicked", self._on_edit_global_webs)

        edit_res_btn = self._make_text_icon_button("Recursos programa", "document-edit-symbolic")
        edit_res_btn.connect("clicked", self._on_edit_program_resources)

        del_btn = self._make_text_icon_button("Eliminar programa", "user-trash-symbolic")
        del_btn.connect("clicked", self._on_delete_program)

        buttons.append(back_btn)
        buttons.append(save_btn)
        buttons.append(reload_btn)
        buttons.append(add_btn)
        buttons.append(webs_btn)
        buttons.append(edit_res_btn)
        buttons.append(del_btn)
        box.append(buttons)
        return scroller

    def _build_bottom_status(self) -> Gtk.Widget:
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        outer.set_margin_top(0)
        outer.set_margin_bottom(18)
        outer.set_margin_start(24)
        outer.set_margin_end(24)

        frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        frame.add_css_class("card")
        frame.add_css_class("panel")

        title = Gtk.Label(label="Estado y registro")
        title.add_css_class("section-title")
        title.set_xalign(0.0)
        frame.append(title)

        self.status_summary = Gtk.Label(label="En espera")
        self.status_summary.set_xalign(0.0)
        self.status_summary.set_wrap(True)
        frame.append(self.status_summary)

        self.log_view = Gtk.TextView()
        self.log_view.set_editable(False)
        self.log_view.set_cursor_visible(False)
        self.log_view.set_monospace(True)
        self.log_view.add_css_class("mono")

        scroller = Gtk.ScrolledWindow()
        scroller.set_hexpand(True)
        scroller.set_vexpand(False)
        scroller.set_min_content_height(170)
        scroller.set_child(self.log_view)
        frame.append(scroller)

        outer.append(frame)
        return outer

    def _append_log(self, text: str) -> None:
        buffer = self.log_view.get_buffer()
        current = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        buffer.set_text(current + f"[{timestamp}] {text}\n")
        end_iter = buffer.get_end_iter()
        buffer.place_cursor(end_iter)
        self.log_view.scroll_to_iter(end_iter, 0.0, False, 0.0, 1.0)

    def _append_log_from_thread(self, text: str) -> bool:
        self._append_log(text)
        return False

    def _clear_runtime_state_css(self) -> None:
        self.status_summary.remove_css_class("status-ok")
        self.status_summary.remove_css_class("status-warn")
        self.status_summary.remove_css_class("status-err")

    def _set_runtime_state(self, title: str, detail: str, level: str = "warn") -> None:
        self.status_summary.set_label(f"{title} — {detail}")
        self._clear_runtime_state_css()
        if level == "ok":
            self.status_summary.add_css_class("status-ok")
        elif level == "err":
            self.status_summary.add_css_class("status-err")
        else:
            self.status_summary.add_css_class("status-warn")

    def _show_message(self, title: str, body: str, message_type: Gtk.MessageType = Gtk.MessageType.INFO) -> None:
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            buttons=Gtk.ButtonsType.OK,
            message_type=message_type,
            text=title,
            secondary_text=body,
        )
        dialog.connect("response", lambda d, _r: d.close())
        dialog.show()

    def _on_reload_config(self, _button) -> None:
        self.env_data = load_env()
        for key, _label in FIELD_SPECS:
            self.config_rows[key].entry.set_text(self.env_data.get(key, DEFAULT_ENV.get(key, "")))
        self._append_log("Configuración recargada desde radio.env")
        self._set_runtime_state("Configuración recargada", "Se han leído de nuevo los valores de radio.env.", "ok")
        self._refresh_status()

    def _on_save_config(self, _button) -> None:
        for key, _label in FIELD_SPECS:
            self.env_data[key] = self.config_rows[key].entry.get_text().strip()
        save_env(self.env_data)
        run_generate_configs()
        self._append_log("Configuración guardada y configuraciones derivadas regeneradas")
        self._set_runtime_state("Configuración guardada", "Se ha actualizado radio.env y se ha regenerado la configuración derivada.", "ok")
        self._refresh_status()
        self._show_message("Configuración guardada", "Se ha actualizado radio.env y se ha ejecutado radio-generate-configs.sh.")

    def _run_stop(self, _button) -> None:
        stop_script = BIN_DIR / "radio-stop.sh"
        if stop_script.exists():
            subprocess.Popen([str(stop_script)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self._append_log("Ejecutado radio-stop.sh")
            self._set_runtime_state("Parando servicios", "Se ha lanzado radio-stop.sh.", "warn")
        else:
            self._append_log("No existe radio-stop.sh")
            self._set_runtime_state("Parada no disponible", "No existe radio-stop.sh.", "err")
        self._refresh_status()

    def _on_action(self, action: dict[str, Any]) -> None:
        kind = action.get("kind", "script")
        if kind == "page":
            target = action.get("target", "panel")
            self.stack.set_visible_child_name(target)
            self._set_runtime_state("Navegación interna", f"Página activa: {target}", "ok")
            return

        script = action.get("script")
        command = None
        action_title = action.get("title", action.get("id", "acción"))
        process_key = action.get("id", script or "accion")

        if kind == "toggle_radiosonde":
            if radiosonde_active():
                script = action.get("script_stop")
                action_title = "Parar radiosonda"
            else:
                script = action.get("script_start")
                action_title = "Arrancar radiosonda"
            process_key = action.get("id", "radiosonde")

        if kind == "toggle":
            if toggle_status_active(action.get("script_status")):
                script = action.get("script_stop")
                action_title = f"Parar {action.get('title', '')}".strip()
            else:
                script = action.get("script_start")
                action_title = f"Arrancar {action.get('title', '')}".strip()
            process_key = action.get("id", "toggle")

        if kind == "toggle_pat":
            if pat_active():
                command = action.get("command_stop")
                action_title = "Parar PAT"
            else:
                script = action.get("script_start")
                action_title = "Arrancar PAT"
            process_key = action.get("id", "pat")

        cmd_args = None
        if command:
            cmd_args = ["bash", "-lc", command]
        elif script:
            script_path = Path(script)
            if not script_path.exists():
                self._show_message("Script no encontrado", f"No existe:\n{script}", Gtk.MessageType.ERROR)
                self._append_log(f"Falta script: {script}")
                self._set_runtime_state("Script no encontrado", script, "err")
                return
            cmd_args = [str(script_path)]

        if not cmd_args:
            self._show_message("Acción inválida", "La acción no tiene script ni comando asociado.", Gtk.MessageType.ERROR)
            return

        shown_target = command if command else script
        self._append_log(f"Lanzando {action_title}: {shown_target}")
        self._set_runtime_state("Arrancando…", f"Ejecutando {action_title}", "warn")
        self._set_buttons_sensitive(False)

        def worker() -> None:
            env = os.environ.copy()
            env["RADIO_PANEL_MODE"] = "1"
            proc = subprocess.Popen(
                cmd_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
            )
            self.processes[process_key] = proc
            assert proc.stdout is not None
            for line in proc.stdout:
                line = line.rstrip()
                if line:
                    GLib.idle_add(self._append_log_from_thread, line)
            rc = proc.wait()
            GLib.idle_add(self._action_finished, {"id": process_key, "title": action_title}, rc)

        threading.Thread(target=worker, daemon=True).start()

    def _action_finished(self, action: dict[str, Any], rc: int) -> bool:
        action_id = action.get("id", "")
        self.processes.pop(action_id, None)
        self._append_log(f"Finalizado {action.get('title', action_id)} con código {rc}")
        if rc == 0:
            self._set_runtime_state("Acción finalizada", f"{action.get('title', action_id)} terminó correctamente.", "ok")
        else:
            self._set_runtime_state("Acción con error", f"{action.get('title', action_id)} terminó con código {rc}.", "err")
        self._refresh_status()
        self._set_buttons_sensitive(True)
        return False

    def _set_buttons_sensitive(self, enabled: bool) -> None:
        pat_on = pat_active()
        occupied = self._occupied_resources()
        for button in self.action_buttons:
            action = button.action
            allowed = action.get("pat_allowed", True)
            can_use = enabled and (allowed or not pat_on)

            tooltip_parts: list[str] = []
            if not allowed and pat_on:
                tooltip_parts.append("Bloqueado mientras PAT esté activo")

            conflicts = self._conflicting_resources(action, occupied)
            if conflicts:
                can_use = False
                tooltip_parts.append("Recursos ocupados: " + ", ".join(conflicts))

            button.set_sensitive(can_use)
            button.set_tooltip_text(" | ".join(tooltip_parts) if tooltip_parts else None)

    def _refresh_status(self) -> None:
        self.env_data = load_env()
        station = (
            f"Indicativo: {self.env_data.get('CALLSIGN', '')}-{self.env_data.get('APRS_SSID', '')}    "
            f"Locator: {self.env_data.get('LOCATOR', '')}    "
            f"Lat/Lon: {self.env_data.get('LAT', '')}, {self.env_data.get('LON', '')}"
        )
        self.station_label.set_label(station)

        pat_on = pat_active()
        rs_on = radiosonde_active()

        if not self.processes:
            if pat_on and rs_on:
                self._set_runtime_state("PAT y radiosonda activos", "Winlink HTTP y auto_rx están en marcha.", "ok")
            elif pat_on:
                self._set_runtime_state("PAT activo", "Winlink HTTP está en marcha.", "ok")
            elif rs_on:
                self._set_runtime_state("Radiosonda activa", "auto_rx está en marcha.", "ok")
            else:
                self._set_runtime_state("En espera", "Listo para lanzar una acción.", "warn")

        self._set_buttons_sensitive(True)
        self._refresh_button_run_states()

    def _poll_state(self) -> bool:
        self._refresh_status()
        return True


class RadioPanelApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.ramon.radio.panel")
        self.connect("activate", self.on_activate)

    def on_activate(self, app: Gtk.Application) -> None:
        ensure_dirs()
        write_default_env()
        write_default_actions()
        write_default_resources()
        write_default_web_links()
        win = self.props.active_window
        if win is None:
            win = RadioPanelWindow(app)
        win.present()


def main() -> None:
    app = RadioPanelApp()
    raise SystemExit(app.run(None))


if __name__ == "__main__":
    main()
