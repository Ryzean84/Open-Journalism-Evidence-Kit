import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from ojek_ledger.cli import main


class CheckpointCliTests(unittest.TestCase):
    def invoke(self, workspace, *arguments):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            result = main(["--workspace", str(workspace), *arguments])
        return result, output.getvalue()

    def test_checkpoint_create_verify_proof_round_trip(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "ledger"
            result, _ = self.invoke(workspace, "init")
            self.assertEqual(result, 0)
            result, _ = self.invoke(
                workspace,
                "add",
                "--url",
                "https://example.org/public-report",
                "--title",
                "Synthetic public report",
                "--publisher",
                "Example Publisher",
            )
            self.assertEqual(result, 0)

            result, output = self.invoke(workspace, "checkpoint", "create")
            self.assertEqual(result, 0, output)
            checkpoint_path = workspace / "exports" / "checkpoint.json"
            self.assertTrue(checkpoint_path.exists())
            checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            self.assertEqual(checkpoint["leaf_count"], 1)

            record_id = checkpoint["leaves"][0]["record_id"]
            result, proof_output = self.invoke(
                workspace,
                "checkpoint",
                "proof",
                str(checkpoint_path),
                "--record-id",
                record_id,
            )
            self.assertEqual(result, 0, proof_output)
            proof_path = workspace / "proof.json"
            proof_path.write_text(proof_output, encoding="utf-8")

            result, verify_output = self.invoke(
                workspace,
                "checkpoint",
                "verify-proof",
                str(proof_path),
                str(checkpoint_path),
            )
            self.assertEqual(result, 0, verify_output)
            self.assertIn('"valid": true', verify_output)

    def test_checkpoint_creation_refuses_invalid_ledger(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "ledger"
            self.assertEqual(self.invoke(workspace, "init")[0], 0)
            self.assertEqual(
                self.invoke(
                    workspace,
                    "add",
                    "--url",
                    "https://example.org/record",
                )[0],
                0,
            )
            record_path = next((workspace / "records").glob("*.json"))
            record = json.loads(record_path.read_text(encoding="utf-8"))
            record["source"]["title"] = "tampered"
            record_path.write_text(json.dumps(record), encoding="utf-8")
            result, output = self.invoke(workspace, "checkpoint", "create")
            self.assertEqual(result, 2)
            self.assertIn("local ledger verification failed", output)


if __name__ == "__main__":
    unittest.main()
