"""Step 3 smoke test: investigate_case returns structured Investigation JSON.

Run from the repository root:

    pip install -r requirements.txt
    $env:AWS_DEFAULT_REGION = "us-east-1"
    $env:BEDROCK_MODEL_ID = "amazon.nova-lite-v1:0"
    python scripts/smoke_investigate_case.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from investigation.investigate import main

if __name__ == "__main__":
    raise SystemExit(main())
