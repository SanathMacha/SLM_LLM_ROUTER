"""Root entrypoint to run the SLM+LLM Cascade Router CLI."""

from __future__ import annotations

import sys
from pathlib import Path

# Allow executing the script directly with correct PYTHONPATH
sys.path.append(str(Path(__file__).resolve().parent))

from src.cli import main

if __name__ == "__main__":
    main()
