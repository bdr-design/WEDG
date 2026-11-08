"""Fails when line coverage in an lcov file is below a floor.

Usage: python3 tool/coverage_floor.py coverage/lcov.info 85
"""
import sys


def main() -> int:
    path, floor = sys.argv[1], float(sys.argv[2])
    found = hit = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("LF:"):
                found += int(line[3:])
            elif line.startswith("LH:"):
                hit += int(line[3:])
    pct = 100.0 * hit / found if found else 0.0
    print(f"line coverage {pct:.1f}% ({hit}/{found}), floor {floor}%")
    return 0 if pct >= floor else 1


if __name__ == "__main__":
    sys.exit(main())
