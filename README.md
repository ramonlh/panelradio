# Radio Panel for Linux

A GTK4 desktop control panel for launching, stopping, and monitoring radio-related applications on Linux.

This project was built to provide a practical **single control panel** for a personal radio station, with support for:

- APRS (`Dire Wolf + YAAC`)
- Digital modes (`fldigi + flrig`)
- WSJT-X
- PAT / Winlink
- Radiosonde / `auto_rx`
- User-defined programs added from the panel itself

The panel is designed for **Linux Mint / Debian-family systems** and uses **Python 3 + GTK4 (PyGObject)**.

---

## Main features

- Large colored buttons for each application
- Start/stop support for fixed applications
- Toggle buttons for applications that can be started and stopped from the same button
- Status area with live log messages
- Optional **RUN** mark on buttons when a program is active
- Built-in configuration page
- Add custom programs from the GUI
- Delete custom programs from the GUI
- Automatic generation of `start`, `stop`, and `status` shell script templates
- Resource-based compatibility system
- Resource catalog management from the GUI
- Assign resources to programs from the GUI
- Prevent launching incompatible programs that need the same hardware/resource

---

## Why this project exists

When several radio programs share the same hardware, audio device, CAT interface, SDR, or serial port, it is easy to start incompatible programs accidentally.

This panel solves that by combining:

1. a simple launcher
2. a program status monitor
3. a resource conflict manager

Instead of manually remembering what can run together, the panel can block incompatible combinations automatically.

---

## Screens and workflow

### Main panel

The main panel shows the operational buttons:

- APRS
- Digital
- WSJT-X
- PAT
- Radiosonde
- user-added programs

Each button can show a visible **RUN** indicator when the corresponding program is active.

### Configuration screen

The configuration screen lets you:

- edit station parameters
- add a new program
- delete a program
- add resources
- delete resources
- edit the resources assigned to each program

The lower log/status area can be hidden in configuration mode to free vertical space.

---

## Directory layout

The project expects this structure under the user home directory:

```text
~/radio/
├── bin/
├── conf/
├── iconos/
├── logs/
└── run/
```

Important files:

```text
~/radio/conf/radio.env
~/radio/conf/actions.json
~/radio/conf/resources.json
~/radio/bin/*.sh
~/radio/logs/*.log
~/radio/run/*.pid
```

---

## Requirements

### System packages

Typical packages needed on Debian / Ubuntu / Linux Mint:

```bash
sudo apt install python3 python3-gi gir1.2-gtk-4.0 curl xdg-utils
```

Depending on your setup, you may also need:

```bash
sudo apt install python3-requests wget
```

### Radio software

Install the programs you want to launch, for example:

- `direwolf`
- Java + `YAAC`
- `fldigi`
- `flrig`
- `wsjtx`
- `pat`
- `python3` for radiosonde tools
- SDR / hardware tools as required by your own station

---

## Running the panel

Start it with:

```bash
python3 radio_panel.py
```

Or create a desktop launcher that points to the script.

---

## Configuration files

### `radio.env`

Stores station and application configuration, for example:

- callsign
- APRS SSID
- coordinates
- locator
- YAAC path
- PAT settings
- ports
- audio defaults

### `actions.json`

Stores all managed program entries, including built-in and user-added programs.

Each program can define things like:

- title
- subtitle
- icon
- color/style
- program kind
- start/stop/status scripts
- whether it is allowed while PAT is active
- resources used

### `resources.json`

Stores the resource catalog used by the compatibility system.

Typical resources might be:

- `hf_rig_audio`
- `hf_rig_cat`
- `vhf_aprs`
- `rtlsdr`
- `serial_ch340`
- `usb_codec`
- `rig_ic7300`

---

## Program kinds

The panel supports several kinds of program entries.

### 1. Standard script program

Single start script:

```json
{
  "id": "example_program",
  "title": "Example",
  "kind": "script",
  "script": "/home/user/radio/bin/example-start.sh"
}
```

### 2. Toggle program

Separate start/stop/status scripts:

```json
{
  "id": "example_toggle",
  "title": "Example Toggle",
  "kind": "toggle",
  "script_start": "/home/user/radio/bin/example-start.sh",
  "script_stop": "/home/user/radio/bin/example-stop.sh",
  "script_status": "/home/user/radio/bin/example-status.sh"
}
```

### 3. Built-in special toggles

Some integrated programs can also use dedicated logic, such as PAT or radiosonde.

---

## Script conventions

Generated templates follow this logic:

### `*-start.sh`

- launches the program
- stores its PID in `~/radio/run`
- writes output to `~/radio/logs`

### `*-stop.sh`

- stops the process using the stored PID
- removes the PID file
- verifies that the program is no longer running

### `*-status.sh`

- returns:
  - `0` if running
  - `1` if stopped

This is critical for reliable RUN indicators and toggle behavior.

---

## Adding a new program

From the GUI:

1. open **Configurar**
2. choose **Añadir programa**
3. enter:
   - title
   - subtitle
   - start command
   - type
   - icon
   - color
   - compatible with PAT or not
   - resources used
4. save

The panel automatically creates:

```text
~/radio/bin/<slug>-start.sh
~/radio/bin/<slug>-stop.sh
~/radio/bin/<slug>-status.sh
```

Example:

- title: `SDRAngel`
- generated scripts:
  - `sdrangel-start.sh`
  - `sdrangel-stop.sh`
  - `sdrangel-status.sh`

---

## Deleting a program

From the GUI:

1. open **Configurar**
2. choose **Eliminar programa**
3. select the program
4. optionally delete the generated scripts as well

For safety, only scripts inside `~/radio/bin` are removed automatically.

---

## Resource management

### Add a resource

From the GUI you can add a resource with:

- visible name
- internal ID
- description

Example resources:

- `hf_rig_audio`
- `hf_rig_cat`
- `vhf_aprs`
- `rtlsdr`

### Delete a resource

A resource can also be removed from the GUI.

Optionally, when deleting a resource, the panel can remove that resource from program assignments.

### Edit program resources

You can assign resources to any program, including the preconfigured ones, from the GUI.

This avoids manual JSON editing.

---

## Compatibility logic

When a program is active, its resources are considered **occupied**.

If another program needs any of the same resources, the panel can block it.

Example:

- `fldigi + flrig` uses:
  - `hf_rig_audio`
  - `hf_rig_cat`

- `WSJT-X` also uses:
  - `hf_rig_audio`
  - `hf_rig_cat`

Therefore they should not be started together.

This approach scales better than maintaining explicit lists of incompatible program pairs.

---

## Built-in applications

Typical built-in buttons in the project:

- APRS
- Digital
- WSJT-X
- PAT
- Radiosonde

Their commands, styles, icons, and resource assignments can also be managed through `actions.json`.

---

## Radiosonde notes

Radiosonde launching can include:

- starting `auto_rx`
- opening a Sondehub page
- opening the local web interface after the local server becomes available

This behavior is normally implemented in the radiosonde start script.

---

## Status and log area

The lower status area is used to show:

- current high-level state
- launch results
- stop results
- generated template information
- resource changes
- program add/delete actions

Autoscroll can be enabled so the most recent line is always visible.

---

## Typical workflow

1. Start the panel
2. Launch a radio application
3. See the RUN marker appear on its button
4. Launch compatible software if resources allow it
5. Incompatible buttons remain blocked
6. Use the configuration page to adjust resources or add new programs

---

## Troubleshooting

### A program starts from terminal but not from the panel

Check:

- script permissions:
  ```bash
  chmod +x ~/radio/bin/my-program-start.sh
  ```
- the script path in `actions.json`
- whether the program is blocked by resources
- whether the status script is returning the correct exit code

### RUN marker never appears

Usually this means the `status.sh` script is not correctly detecting the process.

### Toggle always tries to stop instead of start

Usually the status script is returning `0` even when the program is not active.

### A button stays disabled

Check:

- PAT lock logic
- resource conflicts
- tooltip text for the reason

---

## Suggested future improvements

- icon picker from the GUI
- drag-and-drop reordering of program buttons
- categories / tabs
- export/import configuration
- edit program commands after creation
- better browser handling for multi-window radiosonde workflows
- per-program environment variables
- profiles for different stations or radios

---

## License

Use the license that best fits your project.

If you do not already have one, a simple option is `MIT`.

---

## Author

Designed and adapted for a personal radio station workflow on Linux.
