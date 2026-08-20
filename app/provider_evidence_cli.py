"""Verify one exported, hash-only Cloud Run provider receipt offline."""

from __future__ import annotations

from argparse import ArgumentParser
from dataclasses import asdict
from json import dumps, load
from pathlib import Path

from .provider_evidence import ProviderEvidenceError, verify_provider_receipt


def main() -> int:
    parser = ArgumentParser(description="Verify a hash-only Vice CEO provider receipt.")
    parser.add_argument("receipt_file", type=Path, help="Cloud Logging JSON entry exported by the reviewer.")
    parser.add_argument("--pretty", action="store_true", help="Indent verified evidence JSON.")
    args = parser.parse_args()
    with args.receipt_file.open(encoding="utf-8") as receipt_file:
        entry = load(receipt_file)
    try:
        evidence = verify_provider_receipt(entry)
    except ProviderEvidenceError as error:
        print(dumps({"verified": False, "reason_code": str(error)}, sort_keys=True))
        return 1
    print(dumps({"verified": True, "evidence": asdict(evidence)}, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
