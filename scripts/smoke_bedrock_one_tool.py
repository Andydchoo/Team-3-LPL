"""Step 1 smoke test: Bedrock must call get_revenue_case once.

Run from the repository root:

    pip install -r requirements.txt
    $env:AWS_DEFAULT_REGION = "us-east-1"
    $env:BEDROCK_MODEL_ID = "amazon.nova-lite-v1:0"
    python scripts/smoke_bedrock_one_tool.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from investigation.one_tool import main

if __name__ == "__main__":
    raise SystemExit(main())
