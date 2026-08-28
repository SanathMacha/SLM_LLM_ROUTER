"""Dataset loading and validation module for the SLM+LLM router evaluation."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow executing this file directly as a script without PYTHONPATH issues
if __name__ == "__main__" and __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.config import QUERIES_PATH


def load_eval_set() -> list[dict]:
    """Load and validate the evaluation query set from the queries JSON file.
    
    Raises:
        FileNotFoundError: If the queries file does not exist.
        ValueError: If the file content violates dataset shape or keys constraints.
    """
    if not QUERIES_PATH.exists():
        raise FileNotFoundError(f"Evaluation dataset not found at {QUERIES_PATH}")

    with open(QUERIES_PATH, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse evaluation dataset JSON: {e}")

    if not isinstance(data, list):
        raise ValueError("Evaluation dataset must be a JSON array of query objects")

    # Enforce exactly 120 elements
    if len(data) != 120:
        raise ValueError(f"Evaluation dataset must contain exactly 120 items, but got {len(data)}")

    # Enforce schema constraints for every object
    required_keys = {"id", "query", "target_answer"}
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"Item at index {idx} is not a valid JSON object")
        
        missing = required_keys - item.keys()
        if missing:
            raise ValueError(f"Item at index {idx} (ID: {item.get('id', 'unknown')}) is missing required keys: {missing}")

    return data


if __name__ == "__main__":
    print("Running dataset loader smoke tests...")
    
    try:
        dataset = load_eval_set()
        print(f"Successfully loaded {len(dataset)} items from evaluation set.")
        
        # Verify length constraint
        assert len(dataset) == 120, f"Expected exactly 120 items, got {len(dataset)}"
        
        # Verify schema elements in first item
        first_item = dataset[0]
        print("\nFirst Item details:")
        print(f"  ID            : {first_item['id']}")
        print(f"  Query         : {first_item['query']}")
        print(f"  Target Answer : {first_item['target_answer']}")
        print(f"  Category      : {first_item.get('category', 'N/A')}")
        
        # Check all keys are present
        assert "id" in first_item
        assert "query" in first_item
        assert "target_answer" in first_item
        
        print("\nAll dataset smoke tests passed successfully!")
    except Exception as e:
        print(f"Smoke test failed: {e}")
        sys.exit(1)
