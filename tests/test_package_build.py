import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


class PackageBuildTests(unittest.TestCase):
    def test_wheel_contains_all_published_schemas(self):
        repository = Path(__file__).resolve().parents[1]
        expected = {
            "source-observation.v0.1.schema.json",
            "transparency-log-entry.v0.2.schema.json",
            "transparency-tree-head.v0.2.schema.json",
            "transparency-consistency-proof.v0.2.schema.json",
        }
        with tempfile.TemporaryDirectory() as temporary:
            wheel_dir = Path(temporary)
            subprocess.run(
                [
                    sys.executable, "-m", "pip", "wheel", str(repository),
                    "--no-deps", "--wheel-dir", str(wheel_dir),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            wheels = list(wheel_dir.glob("*.whl"))
            self.assertEqual(len(wheels), 1)
            with zipfile.ZipFile(wheels[0]) as archive:
                members = archive.namelist()
            packaged = {
                Path(name).name for name in members
                if "/share/ojek-local-ledger/schemas/" in name
            }
            self.assertTrue(expected.issubset(packaged), expected - packaged)


if __name__ == "__main__":
    unittest.main()
