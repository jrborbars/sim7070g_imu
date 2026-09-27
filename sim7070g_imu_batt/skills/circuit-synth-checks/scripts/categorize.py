"""Categorize KiCad-vs-circuit-synth net differences.

Benign: KiCad prefixes hierarchical net names with '/' (/SIM_CLK vs SIM_CLK).
Real: different base names (VBAT vs GND) or unconnected-* nets.

Usage: python categorize.py <cs.net> <kicad_from_sch.net>
Exit 0 when there are zero real problems, 1 otherwise.
"""
import sys

from cmp_netlists import parse_netlist


def base(name):
    if name.startswith("unconnected-("):
        return None  # floating in KiCad export
    return name[1:] if name.startswith("/") else name


def main(cs_path, kicad_path):
    cs, _ = parse_netlist(cs_path)
    kd, _ = parse_netlist(kicad_path)

    def pinmap(nets):
        m = {}
        for name, nodes in nets.items():
            for rp in nodes:
                m.setdefault(rp, set()).add(name)
        return m

    cs_pins, kd_pins = pinmap(cs), pinmap(kd)
    benign, real = [], []
    for p in sorted(set(cs_pins) & set(kd_pins)):
        a = {base(n) for n in cs_pins[p]}
        b_raw = kd_pins[p]
        b = {base(n) for n in b_raw}
        if None in b:
            real.append((p, sorted(cs_pins[p]), sorted(b_raw), "FLOATING"))
        elif a == b:
            benign.append(p)
        else:
            real.append((p, sorted(cs_pins[p]), sorted(b_raw), "SHORT/RENAME"))
    print("benign (/-prefix only): %d" % len(benign))
    print("real problems: %d" % len(real))
    for p, a, b, kind in real:
        print("  [%s] %-5s pin %-4s  %s -> %s"
              % (kind, p[0], p[1], ",".join(a), ",".join(b)))
    return 0 if not real else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
