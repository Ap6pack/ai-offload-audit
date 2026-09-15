import tempfile
import unittest
from pathlib import Path

from ai_offload_audit.cli import scan_repo, score_context


class TierScoringTests(unittest.TestCase):
    def test_deterministic_validation_prefers_t0(self):
        tier, confidence, signals, rationale = score_context(
            "validate JSON schema, normalize IPv4/CIDR, calculate checksum"
        )
        self.assertEqual(tier, "T0")
        self.assertGreater(confidence, 0.5)

    def test_narrow_classification_prefers_t1(self):
        tier, confidence, signals, rationale = score_context(
            "classify request intent into one of four labels and route it"
        )
        self.assertEqual(tier, "T1")

    def test_scanner_finds_model_call(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / "app.py").write_text(
                '''\ndef normalize_event(client, payload):\n    """Normalize JSON fields and validate schema."""\n    return client.responses.create(model="example", input=payload)\n''',
                encoding="utf-8",
            )
            findings = scan_repo(repo, 18, 2_000_000, {".py"}, set())
            self.assertTrue(findings)
            self.assertEqual(findings[0].candidate_tier, "T0")


if __name__ == "__main__":
    unittest.main()
