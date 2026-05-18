#!/usr/bin/env python3
import argparse
import ipaddress
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


def is_ip_or_cidr(value: str) -> bool:
    try:
        if "/" in value:
            ipaddress.ip_network(value, strict=False)
        else:
            ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def normalize_domain(value: str):
    value = value.strip().lower()

    if not value:
        return None

    if value.startswith("@"):
        return None

    value = value.split()[0].strip()

    prefixes = [
        "||",
        "domain:",
        "full:",
    ]

    for prefix in prefixes:
        if value.startswith(prefix):
            value = value[len(prefix):].strip()

    value = value.lstrip(".").rstrip("^").rstrip("/").strip()

    if not value:
        return None

    if value.startswith("[") or value.startswith("!") or value.startswith("#"):
        return None

    if value.startswith("regexp:") or value.startswith("include:") or value.startswith("keyword:"):
        return None

    if "*" in value or "/" in value:
        return None

    if is_ip_or_cidr(value):
        return None

    # Keep normal domain-like values only.
    if "." not in value:
        return None

    # Avoid obviously invalid values.
    if any(ch in value for ch in [":", " ", "\t", "\\"]):
        return None

    return value


def parent_domains(domain: str):
    parts = domain.split(".")
    for i in range(1, len(parts) - 1):
        yield ".".join(parts[i:])


def compact_domains(domains):
    ordered = sorted(domains, key=lambda d: (d.count("."), d))

    kept = set()
    for domain in ordered:
        # If a parent suffix is already kept, this subdomain is redundant for ||parent.
        if any(parent in kept for parent in parent_domains(domain)):
            continue
        kept.add(domain)

    return kept


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

    domains = set()
    skipped = 0
    source_names = []

    for input_file in input_files:
        source_names.append(str(input_file))
        for line in input_file.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith(("#", "!", "[")):
                continue

            domain = normalize_domain(line)
            if domain:
                domains.add(domain)
            else:
                skipped += 1

    if not domains:
        raise RuntimeError("No domains generated. Please check source files.")

    compacted = compact_domains(domains)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = [
        "[AutoProxy 0.2.9]",
        "! Title: Direct Rules",
        "! Source: Loyalsoldier/v2ray-rules-dat",
        f"! Tag: {args.tag}",
        f"! Generated: {now}",
        f"! Original Count: {len(domains)}",
        f"! Compact Count: {len(compacted)}",
        f"! Skipped: {skipped}",
        "!",
        *[f"||{domain}" for domain in sorted(compacted)],
    ]

    output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("Input files:")
    for name in source_names:
        print(f"- {name}")
    print(f"Output: {output_file}")
    print(f"Original count: {len(domains)}")
    print(f"Compact count: {len(compacted)}")
    print(f"Skipped: {skipped}")


if __name__ == "__main__":
    main()
