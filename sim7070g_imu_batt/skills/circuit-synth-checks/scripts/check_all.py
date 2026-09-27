#!/usr/bin/env python3
"""Run all circuit-synth design and verification checks in order.

Always run using the project virtual environment:
    ./.venv/bin/python skills/circuit-synth-checks/scripts/check_all.py

Exit 0 if all checks pass, nonzero otherwise.
"""
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCH_PATH = REPO_ROOT / "sim7070g_imu_batt" / "sim7070g_imu_batt.kicad_sch"
CS_NET_PATH = REPO_ROOT / "sim7070g_imu_batt" / "sim7070g_imu_batt.net"
BOM_PATH = REPO_ROOT / "sim7070g_imu_batt" / "sim7070g_imu_batt_bom.csv"
PCB_PATH = REPO_ROOT / "sim7070g_imu_batt" / "sim7070g_imu_batt.kicad_pcb"
BOARD_PY_PATH = REPO_ROOT / "sim7070g_imu_batt" / "board.py"
FOOTPRINTS_DIR = REPO_ROOT / "sim7070g_imu_batt" / "footprints.pretty"
TMP_SCH_NET = Path("/tmp/from_sch.net")
SCRIPTS_DIR = Path(__file__).parent


def run_cmd(args, desc):
    print(f"\n==================================================")
    print(f"▶ {desc}")
    print(f"  Command: {' '.join(str(a) for a in args)}")
    print(f"==================================================")
    res = subprocess.run(args, cwd=REPO_ROOT)
    if res.returncode != 0:
        print(f"❌ FAILED: {desc} (exit code {res.returncode})")
        return False
    print(f"✅ PASSED: {desc}")
    return True


def main():
    py = sys.executable
    checks = [
        # 1. Label collisions
        ([py, str(SCRIPTS_DIR / "check_label_collisions.py"), str(SCH_PATH)],
         "Check 1: Hierarchical Label Collisions"),
        # 2. Netlist export & parity categorization
        (["kicad-cli", "sch", "export", "netlist", "--format", "kicadsexpr", "--output", str(TMP_SCH_NET), str(SCH_PATH)],
         "Check 2a: Export Netlist via kicad-cli"),
        ([py, str(SCRIPTS_DIR / "categorize.py"), str(CS_NET_PATH), str(TMP_SCH_NET)],
         "Check 2b: Netlist Parity (Circuit-Synth vs KiCad Schematic)"),
        # 3. Footprint links and file presence
        ([py, str(SCRIPTS_DIR / "check_symbol_footprint.py"), str(BOARD_PY_PATH), str(FOOTPRINTS_DIR)],
         "Check 3: Symbol Footprint Links"),
        # 4. Footprint loadability in KiCad pcbnew engine
        ([py, str(SCRIPTS_DIR / "check_pcb_loadability.py"), str(BOM_PATH), str(FOOTPRINTS_DIR)],
         "Check 4: KiCad pcbnew Footprint Parser & Pad Validation"),
        # 5. BOM sanity & values
        ([py, str(SCRIPTS_DIR / "check_bom.py"), str(BOM_PATH)],
         "Check 5: BOM Sanity & DNP Allocations"),
        # 7. PCB DRC + schematic parity (unconnected allowed: routing is manual)
        ([py, str(SCRIPTS_DIR / "check_pcb_drc.py"), str(PCB_PATH)],
         "Check 7: PCB DRC & Schematic Parity"),
    ]

    all_ok = True
    for cmd, desc in checks:
        if not run_cmd(cmd, desc):
            all_ok = False
            break

    if not all_ok:
        sys.exit(1)

    print("\n🎉 ALL CIRCUIT-SYNTH & PCB CHECKS PASSED!\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
