# sim7070g_imu_batt — build outputs (regenerate, do not hand-edit)

This folder holds circuit-synth outputs for the 45x35mm daughterboard:
SIM7070G OpenCPU + LSM6DSV16X + ETA6095 (~1A) + 1S LiPo solder pads.

## Regenerate (from repo root, project .venv = Python 3.14.x, no pins)

KICAD_SYMBOL_DIR="./sim7070g_imu_batt:/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols" \
./.venv/bin/python -c "import sim7070g_imu_batt.board as b; c=b.board(); c.generate_kicad_netlist('sim7070g_imu_batt/sim7070g_imu_batt.net'); print(c.generate_text_netlist()[:2000])"

BOM:

KICAD_SYMBOL_DIR="./sim7070g_imu_batt:/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols" \
./.venv/bin/python -c "import sim7070g_imu_batt.board as b; c=b.board(); print(c.generate_bom(project_name='sim7070g_imu_batt'))"

## KiCad workflow (schematic-first, OSS synth has no licensed PCB gen)

Workaround baked into `main.py` (`ensure_pin_number_preference`, runs on
every generation): upstream `circuit_synth/kicad/sch_gen/circuit_loader.py`
identifies pins by NAME first; stock C/R/L pins have empty names and power
pins repeat names, collapsing labels onto pin 1 (102 shorts/floats in KiCad's
own netlist, e.g. C1.1 VBAT->GND). `main.py` rewrites the installed loader
(idempotent no-op once upstream fixes it) to prefer pin NUMBER; after that
KiCad's netlist matches circuit-synth's on all 164 pins (0 real problems,
verified with `kicad-cli sch export netlist` + `cmp_netlists.py`).
Re-create the venv any time (Python 3.14.x, unpinned, pip resolves) — the
fix re-applies automatically. Only GND is exempted from power-symbol
rendering (`Net("GND", is_power=False)` in `board.py`) because the GND
symbol carries no connection semantics beyond the label here.


1. Open `sim7070g_imu_batt.kicad_pro` in KiCad.
2. Symbol libs (`sym-lib-table`): sim7070g / eta6095 / lsm6dsv16x (local
   `.kicad_sym` in this folder) + KiCad stock. Footprints (`fp-lib-table`):
   `footprints.pretty/` (local) + KiCad stock.
3. `LSM6DSV16X_LGA14.kicad_mod` is real geometry from SnapEDA
   XDCR_LSM6DSV16XTR as built in lsm6dsv16x-xiao (verify vs ST datasheet
   mech table before fab).
4. `*_PLACEHOLDER.kicad_mod` files are DO-NOT-FAB outlines only. Draw true
   `SIM7070G_LCC_LGA68` (24x24mm 68-pin LCC+LGA + 0.3mm thermal-via array,
   tented/plugged, per SIM7070 HW Design V1.05), `NanoSIM_PushPush` (MPN
   pads + DET switch), `USB-C-16P` (MPN pads + shell), `BAT_SolderPads`
   (wire-gauge pads + NPTH strain relief) before layout, then replace the
   footprint links in `board.py`.
5. Import `sim7070g_imu_batt.net` into a new 4-layer board
   (L1 Sig / L2 GND continuous / L3 PWR / L4 Sig, 1.6mm FR4) sized 45x35mm
   with 0.6mm castellated edge (TXD/RXD, USB_DP/DM, PWRKEY, RESET_N, BOOT,
   CHG_STAT, BAT+, GND). Layout rules: VBAT 1uF+TVS <2mm then 2x100uF
   <10mm on 1.0-1.5mm copper; RF L1 ref L2, Pi at ANT (series 0R, shunts
   DNP), keepout 3xW, 50R width = TRACE_W_50R_MM tuned to fab + VNA;
   USB 90R dL<0.15mm; SIM module->ESDA6V1->holder <100mm, 100nF+22pF at
   VSIM, DET 10k PU DNP; I2C 4.7k to 1V8; INT via 0R DNP to wake GPIOs.

## Locked electrical facts

ETA6095 (datasheet V1.9, 8p): NO TS/NTC, NO JEITA, NO SYS/power-path.
ISET 0.8V (150k=1.2A, 82k=2A) -> 180k ~= 1A for 1000mAh 1C. CV 4.21V,
precond 2.9V/200mA, term 130mA, recharge -160mV, STAT low=chg/Hi-Z=done,
OTG=GND forces buck. SIM7070G VBAT tied to BAT node for 2A bursts.
VDDIO=1.8V from VDD_EXT reference. MAX17048 + NTC 10k footprints DNP.
