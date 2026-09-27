---
name: circuit-synth-checks
description: Comprehensive verification suite for circuit-synth and KiCad designs (netlists, schematic labels, symbols, footprint syntax, KiCad pcbnew parser, BOM values, DNP rules, ERC, and PCB DRC with schematic parity).
---

# circuit-synth-checks

Comprehensive design and verification suite. All checks must be executed through the project virtual environment (`./.venv/bin/python`).

## Fast All-in-One Verification

Run all checks sequentially with one command:

```sh
./.venv/bin/python skills/circuit-synth-checks/scripts/check_all.py
```

---

## Individual Checks

### 1. Label Collisions (catches shorts in generated schematics)

```sh
./.venv/bin/python skills/circuit-synth-checks/scripts/check_label_collisions.py \
  sim7070g_imu_batt/sim7070g_imu_batt.kicad_sch
```
- **Pass criterion**: `coords with 2+ DIFFERENT net names: 0`.
- Detects overlapping pins/labels that cause KiCad to short unrelated nets together.

### 2. Netlist Parity (Circuit-Synth vs KiCad Schematic Export)

```sh
kicad-cli sch export netlist --format kicadsexpr \
  --output /tmp/from_sch.net sim7070g_imu_batt/sim7070g_imu_batt.kicad_sch
./.venv/bin/python skills/circuit-synth-checks/scripts/categorize.py \
  sim7070g_imu_batt/sim7070g_imu_batt.net /tmp/from_sch.net
```
- **Pass criterion**: `real problems: 0`.
- Distinguishes benign KiCad hierarchical prefixes (`/NET` vs `NET`) from true electrical shorts or broken nets.

### 3. Symbol ↔ Footprint Links & Existence

```sh
./.venv/bin/python skills/circuit-synth-checks/scripts/check_symbol_footprint.py \
  sim7070g_imu_batt/board.py sim7070g_imu_batt/footprints.pretty \
  /Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints
```
- **Pass criterion**: Every footprint link resolves to an existing file, and local footprint pad counts cover the symbol pins.

### 4. PCB Footprint Loadability & C-Engine Syntax Validation

```sh
./.venv/bin/python skills/circuit-synth-checks/scripts/check_pcb_loadability.py \
  sim7070g_imu_batt/sim7070g_imu_batt_bom.csv sim7070g_imu_batt/footprints.pretty
```
- **Pass criterion**: All footprints successfully parse inside KiCad's C++ `pcbnew` engine.
- Catches syntax issues in `.kicad_mod` files (such as naked via declarations inside footprints, duplicate attributes, or malformed S-expressions) before layout or routing.

### 5. BOM Sanity & DNP Allocations

```sh
./.venv/bin/python skills/circuit-synth-checks/scripts/check_bom.py \
  sim7070g_imu_batt/sim7070g_imu_batt_bom.csv
```
- **Pass criterion**: Locked design values (`R1` 180k, `R2/R3` 5.1k, `R4/R5` 1k, `R8/R9` 0R, `L1` 2.2uH) match specifications and all 10 DNP components are properly marked.

### 6. ERC Triage

```sh
kicad-cli sch erc --output /tmp/erc.rpt \
  sim7070g_imu_batt/sim7070g_imu_batt.kicad_sch
```
- **Pass criterion**: 0 `pin_to_pin` errors and 0 `multiple_net_names` errors.

### 7. PCB DRC & Schematic Parity

```sh
./.venv/bin/python skills/circuit-synth-checks/scripts/check_pcb_drc.py
```
- Runs `kicad-cli pcb drc --format json --severity-all --schematic-parity`.
- **Pass criterion**: 0 DRC errors (clearance, shorts, edge clearance...) and 0 parity issues (PCB in sync with schematic: FPIDs, fields `dnp`/`hierarchy_path`/`project_name`/`root_uuid`, DNP and exclude_from_bom attributes).
- Unconnected (ratsnest) items do not fail: routing is manual. Use `--require-routed` after routing completes. Use `--strict` to also fail on warnings (silk, text height).
- Custom DRC rules live in `sim7070g_imu_batt/sim7070g_imu_batt.kicad_dru` (e.g. `U3_LGA14_intra_footprint_pad_gap` for the 0.05 mm LGA14 pad gap).

