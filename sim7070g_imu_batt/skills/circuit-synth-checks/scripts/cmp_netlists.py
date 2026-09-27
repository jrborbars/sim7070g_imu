"""Compare the circuit-synth netlist against KiCad's own netlist export.

Usage: python cmp_netlists.py <cs.net> <kicad_from_sch.net>

Both files are KiCad s-expression netlists; we extract net ->
set of (ref, pin) and diff them. This is the decisive test of whether the
generated schematic preserves the electrical intent.
"""
import re
import sys
from collections import defaultdict


def tokenize(text):
    """Minimal s-expression reader -> nested lists."""
    toks = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', text)
    stack = [[]]
    for t in toks:
        if t == "(":
            new = []
            stack[-1].append(new)
            stack.append(new)
        elif t == ")":
            stack.pop()
        else:
            if t.startswith('"'):
                t = t[1:-1].replace('\\"', '"')
            stack[-1].append(t)
    return stack[0]


def walk(node, tag):
    if isinstance(node, list):
        if node and node[0] == tag:
            yield node
        for child in node:
            yield from walk(child, tag)


def find_one(node, tag):
    for e in node:
        if isinstance(e, list) and e and e[0] == tag:
            return e
    return None


def parse_netlist(path):
    tree = tokenize(open(path, encoding="utf-8", errors="replace").read())
    nets = {}
    order = []
    for netnode in walk(tree, "net"):
        name = find_one(netnode, "name")
        name = name[1] if name else "?"
        nodes = set()
        for n in walk(netnode, "node"):
            ref = find_one(n, "ref")
            pin = find_one(n, "pin")
            if ref and pin:
                nodes.add((ref[1], pin[1]))
        if name not in nets:
            order.append(name)
        nets.setdefault(name, set()).update(nodes)
    return nets, order


def main(cs_path, kicad_path):
    cs, _ = parse_netlist(cs_path)
    kd, _ = parse_netlist(kicad_path)
    print("circuit-synth nets: %d   KiCad-from-sch nets: %d"
          % (len(cs), len(kd)))

    cs_nodes = sum(len(v) for v in cs.values())
    kd_nodes = sum(len(v) for v in kd.values())
    print("circuit-synth nodes: %d  KiCad-from-sch nodes: %d"
          % (cs_nodes, kd_nodes))

    # Build pin -> net maps (a pin must belong to exactly one net).
    def pinmap(nets):
        m = defaultdict(set)
        for name, nodes in nets.items():
            for rp in nodes:
                m[rp].add(name)
        return m

    cs_pins = pinmap(cs)
    kd_pins = pinmap(kd)
    print("circuit-synth pins covered: %d  KiCad pins covered: %d"
          % (len(cs_pins), len(kd_pins)))

    missing = sorted(set(cs_pins) - set(kd_pins))
    extra = sorted(set(kd_pins) - set(cs_pins))
    print("\npins in circuit-synth but absent from KiCad export: %d"
          % len(missing))
    for p in missing[:40]:
        print("   MISSING %-6s pin %-5s (should be on %s)"
              % (p[0], p[1], ",".join(sorted(cs_pins[p]))))
    print("pins in KiCad export but absent from circuit-synth: %d"
          % len(extra))
    for p in extra[:20]:
        print("   EXTRA   %-6s pin %-5s (on %s)"
              % (p[0], p[1], ",".join(sorted(kd_pins[p]))))

    # Pins that changed net name (shorts / renames) - the dangerous case.
    changed = []
    for p in sorted(set(cs_pins) & set(kd_pins)):
        if cs_pins[p] != kd_pins[p]:
            changed.append((p, sorted(cs_pins[p]), sorted(kd_pins[p])))
    print("\npins whose net name changed: %d" % len(changed))
    for p, a, b in changed[:40]:
        print("   %-6s pin %-5s  %s  ->  %s"
              % (p[0], p[1], ",".join(a), ",".join(b)))

    return 0 if not (missing or extra or changed) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
