#!/usr/bin/env python3
"""Verify that KiCad pcbnew can parse every local and stock footprint used in the project.

This catches syntax incompatibilities in .kicad_mod files (e.g. unsupported via tokens,
illegal attr duplicates, unescaped quotes) before PCB placement or routing.

Usage:
    ./.venv/bin/python skills/circuit-synth-checks/scripts/check_pcb_loadability.py <bom_csv> <local_footprints_dir>

Exit 0 when all footprints load cleanly in KiCad, 1 otherwise.
"""
import csv
import os
import subprocess
import sys
from pathlib import Path

DEFAULT_KICAD_PYTHON = "/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3"
DEFAULT_STOCK_DIR = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"


def main():
    if len(sys.argv) < 3:
        print("Usage: check_pcb_loadability.py <bom.csv> <footprints.pretty/> [<stock_dir>]")
        sys.exit(2)

    bom_csv = Path(sys.argv[1]).resolve()
    local_dir = Path(sys.argv[2]).resolve()
    stock_dir = Path(sys.argv[3]).resolve() if len(sys.argv) > 3 else Path(DEFAULT_STOCK_DIR)

    if not bom_csv.exists():
        print(f"BOM not found: {bom_csv}")
        sys.exit(1)

    # Collect unique footprints from BOM
    fps = set()
    with open(bom_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fp = row.get("Footprint")
            if fp:
                fps.add(fp.strip())

    print(f"Validating {len(fps)} unique footprints against KiCad pcbnew...")

    # We call KiCad's bundled Python because pcbnew C-extension requires KiCad's internal framework runtime
    script = f"""
import pcbnew, sys, os

local_dir = r'{local_dir}'
stock_dir = r'{stock_dir}'
fps = {sorted(list(fps))}

failed = []
for fp_str in fps:
    lib, name = fp_str.split(':', 1)
    if lib == 'sim7070g_imu_batt':
        dir_path = local_dir
    else:
        dir_path = os.path.join(stock_dir, lib + '.pretty')

    try:
        fp = pcbnew.FootprintLoad(dir_path, name)
        if fp is None:
            print(f"  FAIL: {{fp_str}} returned None from {{dir_path}}")
            failed.append(fp_str)
        else:
            print(f"  OK:   {{fp_str}} (pads: {{len(list(fp.Pads()))}})")
    except Exception as e:
        print(f"  EXC:  {{fp_str}} -> {{e}}")
        failed.append(fp_str)

if failed:
    print(f"\\n❌ {{len(failed)}} footprints failed to load in pcbnew!")
    sys.exit(1)
else:
    print(f"\\n✅ All {{len(fps)}} footprints loaded cleanly in pcbnew!")
    sys.exit(0)
"""

    kicad_py = DEFAULT_KICAD_PYTHON
    if not Path(kicad_py).exists():
        # Fallback search
        cand = list(Path("/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions").glob("*/bin/python3"))
        if cand:
            kicad_py = str(cand[0])

    res = subprocess.run([kicad_py, "-c", script])
    sys.exit(res.returncode)


if __name__ == "__main__":
    main()
