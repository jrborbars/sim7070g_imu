#!/usr/bin/env python3
"""Check 6: PCB DRC + schematic parity via kicad-cli.

Usage (always from project venv python):
    ./.venv/bin/python skills/circuit-synth-checks/scripts/check_pcb_drc.py [options]

Runs `kicad-cli pcb drc --format json --severity-all --schematic-parity` and applies policy:
  - FAIL on any DRC violation with severity "error" (shorts, clearance, edge, etc.).
  - FAIL on any schematic-parity issue (PCB out of sync with schematic).
  - FAIL on unconnected items only when --require-routed is given (routing is manual).
  - Warnings (silk, text height, ...) are reported but do not fail unless --strict.

Exit 0 if policy passes, nonzero otherwise.
"""
import argparse
import json
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_BOARD = REPO_ROOT / "sim7070g_imu_batt" / "sim7070g_imu_batt.kicad_pcb"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("board", nargs="?", default=str(DEFAULT_BOARD), help="path to .kicad_pcb")
    ap.add_argument("--require-routed", action="store_true",
                    help="fail if unconnected (ratsnest) items remain")
    ap.add_argument("--strict", action="store_true",
                    help="fail on warnings too (except unconnected unless --require-routed)")
    args = ap.parse_args()

    board = Path(args.board)
    if not board.exists():
        print(f"FAIL: board not found: {board}")
        return 2

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        out = Path(tmp.name)

    cmd = ["kicad-cli", "pcb", "drc", "--format", "json",
           "--severity-all", "--schematic-parity", "--output", str(out), str(board)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if not out.exists():
        print(f"FAIL: kicad-cli pcb drc did not produce a report (exit {res.returncode})")
        print((res.stderr or res.stdout).strip()[:500])
        return 2

    d = json.loads(out.read_text())
    out.unlink(missing_ok=True)

    violations = d.get("violations", [])
    parity = d.get("schematic_parity", [])
    unconnected = d.get("unconnected_items", [])

    errors = [v for v in violations if v.get("severity") == "error"]
    warnings = [v for v in violations if v.get("severity") != "error"]

    print(f"board: {board.relative_to(REPO_ROOT)}")
    print(f"  DRC violations : {len(violations)} "
          f"({len(errors)} error, {len(warnings)} warning)")
    print(f"  parity issues  : {len(parity)}")
    print(f"  unconnected    : {len(unconnected)}")

    def show(items, label, n=5):
        c = Counter(i.get("type", "?") for i in items)
        if c:
            print(f"  {label}: {dict(c)}")
        for i in items[:n]:
            print(f"    - [{i.get('type')}] {i.get('description', '')[:110]}")
        if len(items) > n:
            print(f"    ... {len(items) - n} more")

    ok = True
    if errors:
        ok = False
        print("FAIL: DRC errors:")
        show(errors, "errors")
    if parity:
        ok = False
        print("FAIL: schematic parity issues:")
        show(parity, "parity")
    if unconnected:
        if args.require_routed:
            ok = False
            print("FAIL: unconnected items (--require-routed):")
            show(unconnected, "unconnected")
        else:
            print("NOTE: unconnected items present (manual routing pending, not a failure)")
    if warnings:
        show(warnings, "warnings")
        if args.strict:
            ok = False
            print("FAIL: warnings present (--strict)")

    print("PASS: PCB DRC policy" if ok else "FAIL: PCB DRC policy")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
