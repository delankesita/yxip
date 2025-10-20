#!/usr/bin/env python3
import argparse
import re
from pathlib import Path


def iter_lines(path: Path):
    if not path.exists():
        raise SystemExit(f"Log file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            yield line.rstrip("\n")


def main():
    parser = argparse.ArgumentParser(description="Audit log viewer for collect_ips")
    parser.add_argument("--log", default="audit.log", help="Path to audit.log")
    parser.add_argument("--grep", default=None, help="Filter lines by substring or regex")
    parser.add_argument("--level", default=None, help="Minimum level filter (INFO/ERROR)")
    args = parser.parse_args()

    level = (args.level or "").upper()
    pat = args.grep
    rx = None
    if pat:
        try:
            rx = re.compile(pat)
        except re.error:
            rx = None

    for line in iter_lines(Path(args.log)):
        if level and level not in line:
            continue
        if rx is not None:
            if not rx.search(line):
                continue
        elif pat and pat not in line:
            continue
        print(line)


if __name__ == "__main__":
    main()
