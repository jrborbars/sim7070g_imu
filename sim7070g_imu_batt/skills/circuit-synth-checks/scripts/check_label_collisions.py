"""Check for hierarchical-label collisions in a generated .kicad_sch.

Every (hierarchical_label "NET" (at x y ...)) must sit on exactly one
net's pins. If two DIFFERENT net names share one coordinate, KiCad merges
the nets -> a short in the exported netlist (e.g. C1.1 VBAT+ GND).

Usage: python check_label_collisions.py <file.kicad_sch>
Exit 0 when zero colliding coordinates, 1 otherwise.
"""
import re
import sys
from collections import defaultdict


def main(path):
    text = open(path, encoding="utf-8", errors="replace").read()
    labs = re.findall(
        r'\(hierarchical_label\s+"([^"]+)"\s+'
        r'\(shape\s+\w+\)\s+\(at\s+([0-9.+-]+)\s+([0-9.+-]+)',
        text,
    )
    print("hierarchical labels: %d" % len(labs))
    pos = defaultdict(set)
    for name, x, y in labs:
        pos[(round(float(x), 2), round(float(y), 2))].add(name)
    bad = [(k, sorted(v)) for k, v in pos.items() if len(v) > 1]
    print("coords with 2+ DIFFERENT net names: %d" % len(bad))
    for coord, names in sorted(bad):
        print("  %s %s" % (coord, names))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
