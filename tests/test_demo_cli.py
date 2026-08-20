"""Subprocess contract checks for the local, zero-effect demo CLI."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


class DemoCliTests(unittest.TestCase):
    def test_artifact_integrity_mode_emits_the_closed_manifest(self) -> None:
        runtime_root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, "-m", "app.demo_cli", "--artifact-integrity"],
            cwd=runtime_root,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = json.loads(result.stdout)
        self.assertEqual(manifest["manifest_version"], "vice-ceo-demo-artifact-manifest-v1")
        self.assertEqual(manifest["artifact_count"], len(manifest["artifacts"]))
        self.assertEqual(len(manifest["manifest_sha256"]), 64)
        self.assertFalse(manifest["external_effect"])
        self.assertFalse(manifest["persistent_write"])
        self.assertFalse(manifest["production_authority"])
