# ROOMLAB

ROOMLAB is a small, self-hosted, inch-accurate room planner: FastAPI and Uvicorn on the server, plain HTML/CSS/JavaScript and Canvas in the browser, and human-readable JSON on disk. It deliberately resembles graph paper/CAD rather than an interior-design showcase.

## Install on Ubuntu

```bash
sudo apt update
sudo apt install -y python3 python3-venv git
git clone <YOUR-REPOSITORY-URL> roomlab
cd roomlab
./install.sh
```

The installer creates an isolated `.venv` and installs the `roomlab` command. Start locally:

```bash
.venv/bin/roomlab serve
```

Open **http://127.0.0.1:8787**. To listen on the LAN:

```bash
.venv/bin/roomlab serve --host 0.0.0.0 --port 8787
```

Binding to `0.0.0.0` makes the service reachable from the network. There is no authentication: do not expose it directly to the public internet. Use an Ubuntu firewall plus a trusted VPN or authenticated reverse proxy.

## The tool

- Enter dimensions such as `9 ft`, `9’ 11”`, `11.5 ft`, `119 inches`, or centimeters. Model and geometry values remain inches regardless of display units.
- Drag catalog pieces onto the scalable/pannable Canvas; zoom with the wheel. Grid choices are 1/3/6/12 inches with optional snapping.
- Edit footprint, position, name and clearance; rotate, duplicate, delete, center, or wall-align. Keyboard controls: **R**, **Delete**, **Ctrl/Cmd+D**, arrows, Shift+arrows, and Escape.
- Select measurement mode and two points. Selected objects report all four wall clearances and a heuristic fit result.
- Add doors, windows, closets, openings, radiators, fireplaces, and columns. Doors have an architectural swing indication.
- **Smart Arrange** opens a Layout Lab with up to three meaningfully different,
  explainable arrangements. Preview is non-destructive; Apply commits the
  candidate, stores compare variants, autosaves it, and creates one undo step.
- Optional access-zone overlays show bed approaches, desk chair/work space,
  dresser/storage service space, and closet clearance. These planning envelopes
  affect usability scoring but are not furniture or building-code claims.
- Undo/redo covers meaningful furniture, feature, room, drag, and Smart Arrange
  changes (`Ctrl/Cmd+Z` and `Ctrl/Cmd+Shift+Z`; mobile commands are under More).
- Save/autosave JSON projects, load, duplicate, delete, export JSON, and export Canvas PNG. Data defaults to `~/.roomlab/projects`; set `ROOMLAB_DATA` to relocate it.
- Custom catalog dimensions persist in `~/.roomlab/custom_furniture.json`.
- On phones, open **Furniture**, tap one catalog row, then use the persistent
  **Add to Room** footer. The footer remains visible while the catalog scrolls;
  adding creates one centered, selected item and closes the sheet.
- Client-created furniture and features use browser UUIDs when available and a
  dependency-free collision-resistant fallback otherwise, so editing continues
  to work when ROOMLAB is opened from an HTTP server address. Mobile status
  messages are transient and disappear completely instead of leaving a
  permanent “Ready” overlay.

Default dimensions are planning defaults, not claims about every real furniture product and not building-code advice.

### Wall feature coordinates

Wall-bound features store `position` as inches from a consistent wall start: north
and south begin at the left/west corner; east and west begin at the top/north
corner. A feature must fit completely on its wall. The editor validates wall,
width, position, hinge, and swing together before changing project state.

## CLI

```bash
roomlab                         # same as serve
roomlab serve --host 0.0.0.0 --port 8787
roomlab furniture
roomlab projects
roomlab project create "Bedroom"
roomlab project list
roomlab project delete "Bedroom"
roomlab version
roomlab open
```

When not activating the environment, prefix commands with `.venv/bin/`.

## Run persistently with systemd

Create `/etc/systemd/system/roomlab.service` (replace `YOUR_USER` and paths):

```ini
[Unit]
Description=ROOMLAB room planner
After=network.target

[Service]
Type=simple
User=YOUR_USER
WorkingDirectory=/home/YOUR_USER/roomlab
Environment=ROOMLAB_DATA=/home/YOUR_USER/.roomlab
ExecStart=/home/YOUR_USER/roomlab/.venv/bin/roomlab serve --host 0.0.0.0 --port 8787
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now roomlab
sudo systemctl status roomlab
sudo systemctl restart roomlab
sudo systemctl stop roomlab
journalctl -u roomlab -f
```

## Development and tests

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
pytest
roomlab serve --reload
```

## Current limitations

- Shift-click multi-selection supports edge/center alignment and horizontal/vertical distribution; dragging a selected group as one unit is not yet included.
- Wall features use a compact editor and property inspector. Columns remain floor rectangles.
- Smart Arrange targets rectangular rooms and axis-aligned furniture. It models
  one primary bed, up to two nightstands, and the first dresser and desk in
  detail; additional pieces remain fixed while candidates are evaluated.
- Measurement is point-to-point; selected-item wall distances are automatic, while explicit edge-to-edge furniture measurement is not yet a separate mode.
- PDF export, authentication, collaboration, and photorealistic/3D rendering are intentionally absent.

## Structure

`roomlab/geometry.py` and `layout.py` contain reusable measurement/layout logic; `storage.py` owns safe JSON persistence; `server.py` exposes the API; `static/` is the no-build browser application; and `tests/` covers parsing, geometry, layout, and asset/API delivery.

## Semantic layout analysis

Catalog objects now describe their wall preference, anchor/access edge, directional clearances, window behavior, centering preference, and relationships. The generator uses that metadata (with name-based compatibility defaults for older saved projects) to produce meaningful bed offsets, optional bedside-table arrangements, wall-segment-aware dresser positions, and an explainable score breakdown. Door openings and inward swing sectors are scored separately; windows remain usable wall segments but apply semantic obstruction penalties.

Circulation is an intentionally conservative planning approximation, not a code determination. A 3-inch occupancy grid uses breadth-first search from the primary doorway into the central open area and reports entry status plus approximate minimum walkway. The UI also keeps the distinct physical-fit and usability judgments.
