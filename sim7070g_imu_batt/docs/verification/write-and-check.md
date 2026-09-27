# Writing and checking circuit-synth boards (this repo's rules)

## File layout — what lives where

| Path | Role | Hand-edit? |
|---|---|---|
| `sim7070g_imu_batt/board.py` | Sole source of the electrics (Components + Nets) | yes |
| `sim7070g_imu_batt/*.kicad_sym` | Local symbols (SIM7070G 68-pin, ETA6095, LSM6DSV16X, NanoSIM, LDO) | yes |
| `sim7070g_imu_batt/footprints.pretty/*.kicad_mod` | Local footprints | yes |
| `sim7070g_imu_batt/main.py` | Generation entry point + upstream workaround | yes |
| `*.net`, `*.json`, `*.csv`, `*.kicad_sch`, `*.kicad_pro` | Generated outputs | **never** |

## Authoring rules for `board.py`

1. **Always connect by pin NUMBER as a string** — `modem["55"] += vbat`,
   never `modem["VBAT"]`. Rationale: circuit-synth's schematic loader
   (`kicad/sch_gen/circuit_loader.py`) used to identify pins by NAME
   first; stock passives (`Device:C/R/L`) have *empty* names (`""`), so
   both pins collapsed onto pin 1's position — 102 real shorts/floats in
   KiCad's netlist (e.g. `C1 pin 1 VBAT -> GND`, `C1 pin 2 -> floating`).
   `main.py::ensure_pin_number_preference()` rewrites the installed
   loader to prefer NUMBER (idempotent; re-applies after venv rebuilds).
2. **GND is label-only**: `Net("GND", is_power=False, power_symbol=None)`.
3. **DNP** via `dnp=True` on the Component (not a value hack).
4. **Footprint links** are `lib:Name`; local lib is `sim7070g_imu_batt`
   (resolved by `fp-lib-table`), stock libs resolve against KiCad stock.
   Footprint pad numbers must equal symbol pin numbers (except the
   documented SIM7070G duplicates: GND→2 ×15, VBAT→55 ×3, centre pad 2).

## Verification (mirrors `skills/circuit-synth-checks/SKILL.md`)

1. `check_label_collisions.py` on the `.kicad_sch` → 0 colliding coords.
2. `kicad-cli sch export netlist` + `categorize.py` cs.net vs KiCad net →
   0 real problems (current: 164 benign `/-prefix`, 0 real).
3. `check_symbol_footprint.py` → all links resolve.
4. `check_bom.py` → locked values (R1 180k, R2/R3 5.1k, R4/R5 1k,
   R8/R9 0R, L1 2.2uH; DNP C12–C15, D4, R7, R10, R11, RT1, U6).
5. `kicad-cli sch erc` → only known-informational categories.

## Datasheets that constrain this board

- SIM7070 HW Design V1.03: Table 3 (68-pin map), check lists 43/44
  (I2C 1k pull-ups, VBAT >2mm, TVS <3pF USB / <50pF SIM, PI on LTE ANT).
- ETA6095: no TS/NTC, no JEITA, no SYS — 180k ISET ≈ 1A for 1C charge.
- LSM6DSV16X LGA14 pinout from the SnapEDA symbol in
  `lsm6dsv16x-xiao-main.tar.gz`; VDDIO = 1.8V from VDD_EXT (50mA ref).
