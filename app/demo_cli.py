"""Command-line entry point for a recordable, zero-effect demo report."""

from __future__ import annotations

from argparse import ArgumentParser
from dataclasses import asdict
from json import dumps

from .artifact_integrity import build_artifact_integrity_manifest
from .demo_verification import build_demo_verification_report
from .proof_verification import build_proof_verification_report
from .recording_packet import build_recording_packet


def main() -> int:
    parser = ArgumentParser(description="Render the local Vice CEO demo verification report.")
    parser.add_argument("--pretty", action="store_true", help="Indent the JSON output for recording.")
    parser.add_argument(
        "--recording-packet",
        action="store_true",
        help="Render the fixed Devpost reviewer sequence instead of the verification report.",
    )
    parser.add_argument(
        "--proof-verification",
        action="store_true",
        help="Cross-check the local proof-bundle links instead of the verification report.",
    )
    parser.add_argument(
        "--artifact-integrity",
        action="store_true",
        help="Render the closed local source manifest instead of the verification report.",
    )
    args = parser.parse_args()
    selected_modes = sum((args.recording_packet, args.proof_verification, args.artifact_integrity))
    if selected_modes > 1:
        parser.error("choose only one of --recording-packet, --proof-verification, or --artifact-integrity")
    if args.recording_packet:
        print(dumps(asdict(build_recording_packet()), indent=2 if args.pretty else None, sort_keys=True))
        return 0
    if args.proof_verification:
        report = build_proof_verification_report()
        print(dumps(asdict(report), indent=2 if args.pretty else None, sort_keys=True))
        return 0 if report.all_checks_passed else 1
    if args.artifact_integrity:
        manifest = build_artifact_integrity_manifest()
        print(dumps(asdict(manifest), indent=2 if args.pretty else None, sort_keys=True))
        return 0
    report = build_demo_verification_report()
    print(dumps(asdict(report), indent=2 if args.pretty else None, sort_keys=True))
    return 0 if report.all_verified else 1


if __name__ == "__main__":
    raise SystemExit(main())
