#!/usr/bin/env python3
import argparse
from pathlib import Path
from datetime import datetime, timezone


def find_input_files(input_dir: Path):
    files = []
    for item in input_dir.rglob("*"):
        if item.is_file() and item.name not in {".gitkeep"}:
            files.append(item)

    if not files:
        raise FileNotFoundError(f"No source file found in {input_dir}")

    return sorted(files)


def clean_value(value: str):
    value = value.strip()
    if not value:
        return None

    if value.startswith("@"):
        return None

    # Remove common attributes from v2ray geosite text lines.
    # Example: domain:example.com @cn
    value = value.split()[0].strip()

    return value or None


def convert_line(line: str):
    line = line.strip()

    if not line:
        return None

    if line.startswith("#") or line.startswith("!"):
        return None

    if line.startswith("[") and line.endswith("]"):
        return None

    # Keep existing AutoProxy rules.
    if line.startswith("||") or line.startswith("@@"):
        return line

    if line.startswith("regexp:"):
        return None

    if line.startswith("keyword:"):
        value = clean_value(line.removeprefix("keyword:"))
        return value if value else None

    if line.startswith("full:"):
        value = clean_value(line.removeprefix("full:"))
        return f"||{value}" if value else None

    if line.startswith("domain:"):
        value = clean_value(line.removeprefix("domain:"))
        return f"||{value}" if value else None

    if line.startswith("include:"):
        return None

    value = clean_value(line)
    if not value:
        return None

    # Skip IP/CIDR entries. SwitchyOmega domain list does not need them here.
    if "/" in value and any(ch.isdigit() for ch in value):
        return None

    return f"||{value}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_file = Path(args.output)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    input_files = find_input_files(input_dir)

    rules = set()
    skipped = 0
    source_names = []

    for input_file in input_files:
        source_names.append(str(input_file))
        for line in input_file.read_text(encoding="utf-8", errors="ignore").splitlines():
            rule = convert_line(line)
            if rule:
                rules.add(rule)
            elif line.strip() and not line.strip().startswith(("#", "!")):
                skipped += 1

    if not rules:
        raise RuntimeError("No rules generated. Please check source files.")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = [
        "[AutoProxy 0.2.9]",
        "! Title: Direct Rules",
        "! Source: Loyalsoldier/v2ray-rules-dat",
        f"! Tag: {args.tag}",
        f"! Generated: {now}",
        f"! Count: {len(rules)}",
        f"! Skipped: {skipped}",
        "!",
        *sorted(rules),
    ]

    output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("Input files:")
    for name in source_names:
        print(f"- {name}")
    print(f"Output: {output_file}")
    print(f"Count: {len(rules)}")
    print(f"Skipped: {skipped}")


if __name__ == "__main__":
    main()
