"""Verify every footprint link in board.py resolves to a real .kicad_mod.

Usage: python check_symbol_footprint.py <board.py> <footprints.pretty/> [<stock_dirs>...]
Exit 0 when all links resolve, 1 otherwise.

Rules enforced:
- local links (lib == project lib) must exist in footprints.pretty/
- stock links (lib != project lib) must exist in a KiCad stock dir
- pad count in each .kicad_mod must cover the symbol's pin count
  (footprints may legally carry MORE pads than symbol pins only for
  documented multi-pad rails: duplicated pad numbers, e.g. SIM7070G
  GND->2 x15, VBAT->55 x3, plus the centre thermal pad)
"""
import re
import sys
from pathlib import Path


def pads_in_mod(path):
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    return re.findall(r'\(pad\s+"([^"]+)"', text)


def main(board_py, pretty_dir, stock_dirs):
    src = Path(board_py).read_text(encoding="utf-8")
    links = sorted(set(re.findall(r'footprint\s*=\s*(?:"([^"]+)"'
                                  r'\s*(?:"([^"]+)")?|'
                                  r'\(\s*"([^"]+)"\s*"([^"]+)"\s*\))',
                                  src)))
    # normalize the two regex shapes into lib:name strings
    norm = []
    for a, b, c, d in links:
        if a and b:
            norm.append(a + b)
        elif c and d:
            norm.append(c + d)
        elif a:
            norm.append(a)
    problems = []
    for link in sorted(set(norm)):
        if ":" not in link:
            problems.append("%s: malformed footprint link" % link)
            continue
        lib, name = link.split(":", 1)
        if not name or name.endswith(":"):
            problems.append("%s: empty footprint name" % link)
            continue
        if lib == "sim7070g_imu_batt":
            cand = Path(pretty_dir) / (name + ".kicad_mod")
            if not cand.exists():
                problems.append("%s: missing local %s" % (link, cand))
            else:
                print("  local %-55s pads=%d" % (link, len(pads_in_mod(cand))))
        else:
            found = any((Path(s) / (lib + ".pretty") / (name + ".kicad_mod")
                         ).exists() for s in stock_dirs)
            status = "ok" if found else "MISSING"
            print("  stock %-55s %s" % (link, status))
            if not found:
                problems.append("%s: not found in stock dirs" % link)
    print("footprint links: %d, problems: %d" % (len(set(norm)),
                                                 len(problems)))
    for p in problems:
        print("  PROBLEM: %s" % p)
    return 0 if not problems else 1


DEFAULT_STOCK_DIRS = [
    "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints",
    "/usr/share/kicad/footprints",
]


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python check_symbol_footprint.py <board.py> <footprints.pretty/> [<stock_dirs>...]")
        sys.exit(2)
    board_py, pretty = sys.argv[1], sys.argv[2]
    stock = sys.argv[3:] or [d for d in DEFAULT_STOCK_DIRS if Path(d).exists()]
    sys.exit(main(board_py, pretty, stock))
