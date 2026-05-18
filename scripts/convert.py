#!/usr/bin/env python3
import argparse
from pathlib import Path
from datetime import datetime, timezone


def find_input_file(input_dir: Path, tag: str) -> Path:
    candidates = list(input_dir.glob(f"*_{tag}.txt"))
    if not candidates:
        candidates = list(input_dir.glob("*.txt"))
    if not candidates:
        raise FileNotFoundError(f"No txt file found in {input_dir}")
    return candidates[0]


def convert_line(line: str):
    line = line.strip()

    if not line or line.startswith("#"):
        return None

    if line.startswith("regexp:"):
        return None

    if line.startswith("keyword:"):
        value = line.removeprefix("keyword:").strip()
        return value if value else None

    if line.startswith("full:"):
        value = line.removeprefix("full:").strip()
        return f"||{value}" if value else None

    if line.startswith("domain:"):
        value = line.removeprefix("domain:").strip()
        return f"||{value}" if value else None

    return f"||{line}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_file = Path(args.output)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    input_file = find_input_file(input_dir, args.tag)

    rules = set()
    skipped = 0

    for line in input_file.read_text(encoding="utf-8", errors="ignore").splitlines():
        rule = convert_line(line)
        if rule:
            rules.add(rule)
        elif line.strip() and not line.strip().startswith("#"):
            skipped += 1

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = [
        "[AutoProxy 0.2.9]",
        "! Title: Direct Rules",
        "! Source: Loyalsoldier/v2ray-rules-dat geosite.dat",
        f"! Tag: {args.tag}",
        f"! Generated: {now}",
        f"! Count: {len(rules)}",
        f"! Skipped: {skipped}",
        "!",
        *sorted(rules),
    ]

    output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    print(f"Count: {len(rules)}")
    print(f"Skipped: {skipped}")


if __name__ == "__main__":
    main()
