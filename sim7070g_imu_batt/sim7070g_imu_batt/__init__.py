"""SIM7070G (OpenCPU) + LSM6DSV16X + 1S LiPo board, built with circuit-synth.

Locked design decisions
-----------------------
* Charger ETA6095: no TS/NTC, no JEITA, no SYS/load-sharing. ISET 180k ~ 1A
  (1C of the 1000mAh pack), OTG tied to GND, STAT -> castellated test point.
  The module VBAT pins hang directly off the BAT node so 2A TX bursts are
  fed by the pack + the 3x100uF bank, not through a cable-drop-limited rail.
* Module: SIM7070G 24.0x24.0x2.3mm, 68-pad LCC+LGA (pin-compatible geometry
  with SIM7000G). 1.8V logic only; VDD_EXT (pin 15, 50mA) is a reference.
* IMU: LSM6DSV16X on a dedicated nano-Iq 2.5V LDO for VDD, with VDDIO tied
  to the module's 1.8V VDD_EXT so the I/O levels match exactly.
* SIM: VSIM is 1.8V only on the SIM7070G (no 3V legacy), routed through the
  ESDA6V1 pads before the holder, keep under 100mm, 100nF + 22pF at VSIM.
* RF: PI network hard against ANT_MAIN / GNSS_ANT, series 0R populated,
  shunts DNP until VNA tuning.
* Stack: L1 Sig / L2 GND / L3 PWR / L4 Sig, 1.6mm FR4. RF on L1 referenced
  to L2, USB as a 90R pair, VBAT >2mm.

Run the generator with:  python -m sim7070g_imu_batt.main
"""

from circuit_synth import Circuit, Component  # noqa: F401

TRACE_W_50R_MM = 0.35  # param: recompute per fab prepack (Er ~4.2) + VNA
