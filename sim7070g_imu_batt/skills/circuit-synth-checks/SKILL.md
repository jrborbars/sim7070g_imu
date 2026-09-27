---
name: circuit-synth-checks
description: Verify a circuit-synth board (netlists, schematic labels, symbols, footprints, BOM, ERC) before layout or fab. Use after any board.py change and regeneration.
---

# circuit-synth-checks

Five checks, in order. All commands run from the repo root with the
project venv (Python 3.14.x, unpinned deps — pip resolves):

```sh
V=.venv/bin/python
export KICAD_SYMBOL_DIR="./sim7070g_imu_batt:/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols"
```

Regenerate first (applies the pin-number workaround idempotently):

```sh
$V -m sim7070g_imu_batt.main
```

## 1. Label collisions (fastest, catches shorts)

```sh
$V skills/circuit-synth-checks/scripts/check_label_collisions.py \
  sim7070g_imu_batt/sim7070g_imu_batt.kicad_sch
```

**Pass:** `coords with 2+ DIFFERENT net names: 0`.
Two different net names on one coordinate = KiCad merges the nets.
History: 29 collisions (e.g. GND+VBAT on C1 pin 1) caused 102
shorts/floats — see `docs/verification/write-and-check.md`.

## 2. Netlist parity (decisive)

```sh
kicad-cli sch export netlist --format kicadsexpr \
  --output /tmp/from_sch.net sim7070g_imu_batt/sim7070g_imu_batt.kicad_sch
$V skills/circuit-synth-checks/scripts/categorize.py \
  sim7070g_imu_batt/sim7070g_imu_batt.net /tmp/from_sch.net
```

**Pass:** `real problems: 0` (benign `/-prefix` renames are fine —
KiCad prefixes hierarchical nets with `/`).

## 3. Symbol ↔ footprint links

```sh
$V skills/circuit-synth-checks/scripts/check_symbol_footprint.py \
  sim7070g_imu_batt/board.py sim7070g_imu_batt/footprints.pretty \
  /Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints
```

**Pass:** every link resolves; local `.kicad_mod` pad counts cover the
symbol pins. Known exception: `SIM7070G_LCC_LGA68` carries 69 pads for
68 symbol pins — the 15 GND pads share number 2, the 3 VBAT pads share
55, plus the centre thermal pad (also 2). Intentional.

## 4. BOM values

```sh
$V skills/circuit-synth-checks/scripts/check_bom.py \
  sim7070g_imu_batt/sim7070g_imu_batt_bom.csv
```

**Pass:** ISET 180k, CC 5.1k, I2C pull-ups 1k to VDD_EXT, PI series 0R,
L1 2.2uH, and the 10 expected DNPs (C12–C15, D4, R7, R10, R11, RT1, U6).

## 5. ERC triage

```sh
kicad-cli sch erc --output /tmp/erc.rpt \
  sim7070g_imu_batt/sim7070g_imu_batt.kicad_sch
```

**Pass:** only the known-informational categories — hierarchical
labels in the root sheet, unconnected NC/PCM pins, `power_pin_not_driven`
(no PWR_FLAGs by design), and `footprint_link_issues` for the local lib
(which resolves inside the KiCad project, not the bare CLI sandbox).
**Fail:** any `pin_to_pin` or `multiple_net_names` violation.

Full rationale, file layout, and authoring rules:
`docs/verification/write-and-check.md`.
