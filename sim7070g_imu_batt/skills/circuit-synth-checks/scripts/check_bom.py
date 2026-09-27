"""Quick BOM sanity check against the project's locked values.

Usage: python check_bom.py <bom.csv>
Exit 0 when all assertions hold, 1 otherwise.
"""
import csv
import sys


EXPECTED = {
    "R1": "180k",    # ISET ~= 1A for the 1000mAh 1C rate
    "R2": "5.1k",    # USB-C CC sink
    "R3": "5.1k",
    "R4": "1k",      # I2C pull-ups to VDD_EXT (check list #9)
    "R5": "1k",
    "R8": "0R",      # PI series, populated
    "R9": "0R",
    "L1": "2.2uH",
}

EXPECTED_DNP = {"C12", "C13", "C14", "C15",  # PI shunts, VNA tune later
                "D4", "R7", "R10", "R11", "RT1", "U6"}


def main(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    by_ref = {}
    for r in rows:
        for ref in r["Refs"].split(","):
            by_ref[ref.strip()] = r
    problems = []
    for ref, value in EXPECTED.items():
        got = (by_ref.get(ref) or {}).get("Value", "<missing>")
        if got != value:
            problems.append("%s: expected %s, got %s" % (ref, value, got))
    dnp = {ref for ref, r in by_ref.items()
           if (r.get("DNP") or "").lower() == "true"}
    if dnp != EXPECTED_DNP:
        problems.append("DNP set mismatch: missing=%s extra=%s"
                        % (sorted(EXPECTED_DNP - dnp),
                           sorted(dnp - EXPECTED_DNP)))
    print("bom rows: %d  refs: %d  dnp: %d"
          % (len(rows), len(by_ref), len(dnp)))
    for p in problems:
        print("  PROBLEM: %s" % p)
    print("bom check: %s" % ("OK" if not problems else "FAILED"))
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
