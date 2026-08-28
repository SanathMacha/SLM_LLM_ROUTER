"""Deterministic rule-based grading engine for parsing and comparing model predictions."""

from __future__ import annotations

import re
import string
import sys
from pathlib import Path

# Allow executing this file directly as a script without PYTHONPATH issues
if __name__ == "__main__" and __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.config import ANSWER_PREFIX


def extract_answer(text: str) -> str:
    """Extract the answer portion from the model output.
    
    Looks for the ANSWER_PREFIX (e.g. "Answer:"). If found, extracts everything after it.
    If not, falls back to the last non-empty line of the text.
    Strips whitespace, markdown bolding (**), and common punctuation (periods, commas).
    """
    text = text.strip()
    if not text:
        return ""

    if ANSWER_PREFIX in text:
        # Get the part after the first occurrence of ANSWER_PREFIX in the text
        parts = text.split(ANSWER_PREFIX, 1)
        raw_ans = parts[1]
    else:
        # Fall back to the last non-empty line
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        raw_ans = lines[-1] if lines else ""

    # Clean markdown bolding
    raw_ans = raw_ans.replace("**", "")

    # Strip whitespace and common punctuation (periods, commas, etc. at the start/end of the answer)
    # We use a set of characters to strip, including standard punctuation like '.' and ','
    to_strip = string.whitespace + ".,"
    return raw_ans.strip(to_strip)


def normalize_numeric(text: str) -> str:
    """Normalize numeric strings by removing commas, stripping units, and standardizing float format."""
    text = text.strip()
    if not text:
        return ""

    # Remove commas from large numbers (e.g., "1,000" -> "1000")
    # Only remove commas if they are surrounded by digits to avoid breaking sentence lists
    text = re.sub(r'(?<=\d),(?=\d)', '', text)

    # Strip common units and currency symbols
    # Common units: $, %, kg, mph, cm, m, units, years, etc.
    # We can strip leading/trailing symbols
    text = text.strip("$%€£¥")
    
    # Use regex to strip common suffixes like "kg", "mph", "cm", "m", "g", "lbs", "units", "years", "percent"
    # We look for letters/words at the end of the numeric value, possibly separated by a space
    text = re.sub(r'\s*(?:kg|mph|cm|m|g|lbs|units?|years?|percent)\b', '', text, flags=re.IGNORECASE)
    text = text.strip()

    # If the string can be parsed as a float, standardize it
    try:
        val = float(text)
        # Standardize float to remove trailing zeros (e.g., "45.0" -> "45")
        if val.is_integer():
            return str(int(val))
        return str(val)
    except ValueError:
        pass

    return text


def grade_answer(predicted: str, target: str) -> bool:
    """Compare prediction against target using numeric tolerance or exact case-insensitive match."""
    # Extract prediction value
    pred_val = extract_answer(predicted)
    target_val = extract_answer(target)

    # Normalize both values
    pred_norm = normalize_numeric(pred_val)
    target_norm = normalize_numeric(target_val)

    # Try numeric float parsing and comparison within tolerance
    try:
        pred_float = float(pred_norm)
        target_float = float(target_norm)
        return abs(pred_float - target_float) < 1e-5
    except ValueError:
        pass

    # Fallback to case-insensitive exact string match
    return pred_norm.lower() == target_norm.lower()


if __name__ == "__main__":
    print("Running grader smoke tests...")

    # 1. String matching tests with/without prefix
    assert grade_answer("Paris", "Paris") is True, "Exact string match failed"
    assert grade_answer("Answer: Paris", "Paris") is True, "Prefix extraction failed"
    assert grade_answer("Answer: **Paris**.", "Paris") is True, "Punctuation/markdown stripping failed"
    assert grade_answer("The capital is Paris.\nAnswer: Paris", "Paris") is True, "Multi-line extraction failed"
    assert grade_answer("Paris.", "Paris") is True, "Trailing period stripping failed"

    # 2. Numeric equivalence tests
    assert grade_answer("1000", "1,000") is True, "Comma parsing failed"
    assert grade_answer("$1,000.00", "1000") is True, "Currency & float standardization failed"
    assert grade_answer("45.0", "45") is True, "Float trailing zero removal failed"
    assert grade_answer("45.50", "45.5") is True, "Float decimal precision matching failed"
    assert grade_answer("50 kg", "50") is True, "Unit suffix stripping failed"
    assert grade_answer("120%", "1.2") is False, "Percent logic check failed" # 120% normalized should be "120", not "1.2"
    assert grade_answer("120%", "120") is True, "Percent equivalence failed"

    # 3. Fallback matching test
    assert grade_answer("Answer: forty-two", "forty-two") is True, "String fallback match failed"
    assert grade_answer("Answer: Forty-Two", "forty-two") is True, "Case insensitivity check failed"

    print("All grader smoke tests passed successfully!")
