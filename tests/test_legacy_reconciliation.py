import contextlib
import importlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent


class LegacyReconciliationTests(unittest.TestCase):
    def test_imports_perform_no_application_io_or_reporting(self):
        script = '''
from unittest.mock import patch
with patch("builtins.open", side_effect=AssertionError("file I/O on import")), \\
     patch("io.open", side_effect=AssertionError("file I/O on import")), \\
     patch("builtins.print", side_effect=AssertionError("reporting on import")):
    import scripts.reconciliation_engine
    import revenue_engine
'''
        result = subprocess.run([sys.executable, "-c", script], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_pure_reconciliation_preserves_saved_results_and_inputs(self):
        engine = importlib.import_module("scripts.reconciliation_engine")
        inputs = [json.loads((ROOT / "data" / name).read_text()) for name in [
            "advisory_agreements.json", "household_mappings.json", "billing_logs.json",
            "seeded_errors_manifest.json",
        ]]
        original = deepcopy(inputs)
        saved = json.loads((ROOT / "data/reconciliation_results.json").read_text())
        with patch("builtins.open", side_effect=AssertionError("unexpected I/O")), \
                patch("io.open", side_effect=AssertionError("unexpected I/O")):
            result = engine.reconcile(*inputs)
        self.assertEqual(result, saved)
        self.assertEqual(inputs, original)
        self.assertTrue(result["validation"]["all_caught"])
        self.assertEqual(result["validation"]["detected"], 8)

    def test_legacy_cli_writes_explicit_report_to_selected_output_directory(self):
        engine = importlib.import_module("scripts.reconciliation_engine")
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(engine, "OUTPUT_DIR", Path(directory)), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(engine.main(), 0)
            result = json.loads((Path(directory) / "reconciliation_results.json").read_text())
            self.assertEqual(result["validation"]["detected"], 8)


if __name__ == "__main__":
    unittest.main()
