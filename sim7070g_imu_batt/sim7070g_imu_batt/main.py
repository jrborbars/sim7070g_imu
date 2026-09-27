"""Generation entry point for the SIM7070G + LSM6DSV16X + 1S LiPo board.

Usage (always from the repo root, with the project venv - Python 3.14.x):

    KICAD_SYMBOL_DIR="./sim7070g_imu_batt:/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols" \
        ./.venv/bin/python -m sim7070g_imu_batt.main

Outputs land in ./sim7070g_imu_batt/ (netlist, BOM CSV/JSON, KiCad
schematic + project). The OSS build of circuit-synth refuses to generate a
PCB ("PCB generation features are not included in this version"), so layout
is done by hand in KiCad after importing the netlist - see README.md.
"""

import os
import sys

from sim7070g_imu_batt.board import board

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "sim7070g_imu_batt")
PROJECT_NAME = "sim7070g_imu_batt"

# Marker left in the patched loader so re-runs are idempotent.
_PIN_FIX_MARKER = "Pin identification - prefer NUMBER over NAME."


def ensure_pin_number_preference():
    """Work around an upstream circuit-synth schematic bug (verified).

    circuit_synth/kicad/sch_gen/circuit_loader.py builds the schematic
    writer's ``(ref, pin_identifier)`` pairs preferring pin NAME over pin
    NUMBER. Stock passives (Device:C/R/L) have EMPTY names (""), so every
    pin of the part collapses onto pin 1's position: both labels land on
    one pad (short) and the other pad floats. Before the fix, KiCad's own
    netlist of the generated schematic showed 102 real shorts/floats
    (e.g. C1.1 VBAT->GND); after preferring NUMBER it shows 0.

    The venv is disposable (unpinned deps, pip resolves), so this applies
    the string patch to the installed file when the buggy pattern is
    present, and no-ops when upstream fixes it. Safe to run every time.
    Returns True when generation may proceed.
    """
    import importlib.util

    spec = importlib.util.find_spec(
        "circuit_synth.kicad.sch_gen.circuit_loader")
    if spec is None or not spec.origin:
        print("  pin-fix    -> circuit_loader not found, skipping")
        return True
    path = spec.origin
    try:
        text = open(path, encoding="utf-8").read()
    except OSError as exc:
        print("  pin-fix    -> cannot read loader (%s), skipping" % exc)
        return True
    if _PIN_FIX_MARKER in text:
        print("  pin-fix    -> already applied (%s)" % path)
        return True
    buggy = '''            # Enhanced pin identification - store the most specific identifier available
            pin_identifier = None

            # First check if name is available (most specific)
            if "name" in pin_data and pin_data["name"] != "~":
                pin_identifier = pin_data["name"]
                logger.debug(
                    f"Using pin name '{pin_identifier}' for {comp_ref} in net {net_name}"
                )
            # Then check for number
            elif "number" in pin_data:
                pin_identifier = str(pin_data["number"])
                logger.debug(
                    f"Using pin number '{pin_identifier}' for {comp_ref} in net {net_name}"
                )'''
    fixed = '''            # Pin identification - prefer NUMBER over NAME.
            # KiCad pin numbers are unique per symbol and bind to footprint
            # pads. Names are unreliable: stock passives (Device:C/R/L)
            # have EMPTY names (""), which collapses every pin of the part
            # onto the first pin, and power pins repeat names (GND x N,
            # VBUS x N on USB-C; GND x 2 on the IMU). Using the name first
            # places both labels on pin 1's position, shorting nets and
            # leaving the other pins floating in the exported schematic.
            pin_identifier = None

            # First check for number (unique, footprint-binding)
            if "number" in pin_data and str(pin_data["number"]) not in (
                "",
                "~",
            ):
                pin_identifier = str(pin_data["number"])
                logger.debug(
                    f"Using pin number '{pin_identifier}' for {comp_ref} in net {net_name}"
                )
            # Then check if name is available and non-empty
            elif "name" in pin_data and pin_data["name"] not in (
                "",
                "~",
                None,
            ):
                pin_identifier = pin_data["name"]
                logger.debug(
                    f"Using pin name '{pin_identifier}' for {comp_ref} in net {net_name}"
                )'''
    if buggy not in text:
        print("  pin-fix    -> upstream changed (no buggy pattern), skipping")
        return True
    try:
        open(path, "w", encoding="utf-8").write(
            text.replace(buggy, fixed, 1))
    except OSError as exc:
        print("  pin-fix    -> cannot write loader (%s), aborting" % exc)
        return False
    # Drop the stale bytecode so the fixed source is used this run.
    import pathlib
    for pyc in pathlib.Path(path).parent.glob(
            "__pycache__/circuit_loader.*.pyc"):
        try:
            pyc.unlink()
        except OSError:
            pass
    print("  pin-fix    -> applied (prefer pin NUMBER over NAME)")
    return True


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    os.makedirs(OUT_DIR, exist_ok=True)
    # Pre-populate KICAD_SYMBOL_DIR with project symbol dir + stock KiCad
    # so generation succeeds even if the caller omitted the env var.
    stock_syms = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols"
    existing = os.environ.get("KICAD_SYMBOL_DIR", "")
    parts = [p for p in existing.split(os.pathsep) if p]
    if OUT_DIR not in parts:
        parts.insert(0, OUT_DIR)
    if os.path.isdir(stock_syms) and stock_syms not in parts:
        parts.append(stock_syms)
    os.environ["KICAD_SYMBOL_DIR"] = os.pathsep.join(parts)


    if not ensure_pin_number_preference():
        return 1
    circ = board()
    comps = list(circ.components.values())
    print("Built circuit: %s" % circ.name)
    print("  components : %d" % len(comps))
    print("  nets       : %d" % len(circ.nets))

    dnp = sorted(c.ref for c in comps if getattr(c, "dnp", False))
    print("  DNP        : %d (fit-later) %s" % (len(dnp), ", ".join(dnp)))

    net_file = os.path.join(OUT_DIR, "%s.net" % PROJECT_NAME)
    circ.generate_kicad_netlist(net_file)
    print("  netlist    -> %s" % net_file)

    # output_file must be a FILE path; kicad-cli fails if handed a directory.
    bom_file = os.path.join(OUT_DIR, "%s_bom.csv" % PROJECT_NAME)
    bom = circ.generate_bom(output_file=bom_file, project_name=PROJECT_NAME)
    print("  bom        -> %s (%s items)"
          % (bom.get("file", bom_file), bom.get("component_count", "?")))

    # force_regenerate is REQUIRED: circuit-synth's incremental update path
    # raises "'SheetManager' object is not iterable" on an existing sheet.
    try:
        circ.generate_kicad_project(PROJECT_NAME, generate_pcb=False,
                                    force_regenerate=True)
        print("  schematic  -> %s.kicad_sch / .kicad_pro" % PROJECT_NAME)
    except Exception as exc:  # pragma: no cover - depends on local KiCad
        print("  schematic  -> SKIPPED (%s)" % exc)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
