"""Monotonic escalation verifier to control SLM to LLM routing thresholds."""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Allow executing this file directly as a script without PYTHONPATH issues
if __name__ == "__main__" and __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.grader import extract_answer, normalize_numeric


def check_parse_failure(raw_text: str) -> bool:
    """Returns True if the output does not contain a parseable final answer."""
    extracted = extract_answer(raw_text)
    return extracted == ""


def check_type_mismatch(raw_text: str) -> bool:
    """Returns True if the extracted final answer cannot be parsed as a valid numeric float."""
    extracted = extract_answer(raw_text)
    normalized = normalize_numeric(extracted)
    try:
        float(normalized)
        return False
    except ValueError:
        return True


def check_hedging(raw_text: str) -> bool:
    """Returns True if the reasoning trace contains uncertainty or hedging lexicons."""
    # Lexicon patterns: maybe, not sure, unclear, probably, could be, likely, uncertain
    hedging_pattern = re.compile(
        r"\b(maybe|not\s+sure|unclear|probably|could\s+be|likely|uncertain)\b", 
        re.IGNORECASE
    )
    return bool(hedging_pattern.search(raw_text))


def check_disagreement(samples: list[str]) -> bool:
    """Returns True if any two valid extracted consistency samples differ mathematically."""
    valid_norms = []
    for sample in samples:
        extracted = extract_answer(sample)
        normalized = normalize_numeric(extracted)
        if normalized:  # Only track valid, non-empty extracted answers
            valid_norms.append(normalized)

    # Compare every pair
    for i in range(len(valid_norms)):
        for j in range(i + 1, len(valid_norms)):
            v1 = valid_norms[i]
            v2 = valid_norms[j]
            try:
                f1 = float(v1)
                f2 = float(v2)
                if abs(f1 - f2) >= 1e-5:
                    return True
            except ValueError:
                if v1.lower() != v2.lower():
                    return True
    return False


def should_escalate(slm_text: str, slm_samples: list[str], strictness: int) -> tuple[bool, str]:
    """Determine whether to escalate the query to the cloud LLM based on strictness level.
    
    Returns:
        (bool, str): A boolean indicating whether to escalate, and a descriptive log message reason.
    """
    # Level 0: All-SLM floor (never escalate)
    if strictness == 0:
        return False, "Accepted: Level 0 (All-SLM floor)"

    # Level 1: Parse failure
    if check_parse_failure(slm_text):
        return True, "Escalated: Level 1 (Parse failure)"
    if strictness == 1:
        return False, "Accepted: Level 1 checks passed"

    # Level 2: Type mismatch
    if check_type_mismatch(slm_text):
        return True, "Escalated: Level 2 (Constraint / type mismatch)"
    if strictness == 2:
        return False, "Accepted: Level 2 checks passed"

    # Level 3: Hedging/Uncertainty detection
    if check_hedging(slm_text):
        return True, "Escalated: Level 3 (Hedging lexicon detected)"
    if strictness == 3:
        return False, "Accepted: Level 3 checks passed"

    # Level 4: Self-consistency sampling disagreement
    if check_disagreement(slm_samples):
        return True, "Escalated: Level 4 (Sample disagreement)"
    if strictness == 4:
        return False, "Accepted: Level 4 checks passed"

    # Level 5: All-LLM ceiling (always escalate)
    if strictness == 5:
        return True, "Escalated: Level 5 (All-LLM ceiling)"

    raise ValueError(f"Unknown strictness level: {strictness}")


if __name__ == "__main__":
    print("Running verifier smoke tests...")

    # Sample outputs for testing
    clean_out = "We multiply 2 by 2.\nAnswer: 4"
    empty_out = ""
    string_out = "Answer: Paris"
    hedging_out = "I am not sure, maybe it is 4.\nAnswer: 4"
    
    samples_agree = ["Answer: 4", "Answer: 4.0", "Answer: 4"]
    samples_disagree = ["Answer: 4", "Answer: 5", "Answer: 4"]

    # 1. Parse Failure Checks
    assert check_parse_failure(clean_out) is False
    assert check_parse_failure(empty_out) is True

    # 2. Type Mismatch Checks
    assert check_type_mismatch(clean_out) is False
    assert check_type_mismatch(string_out) is True, "Paris cannot be a float"

    # 3. Hedging Checks
    assert check_hedging(clean_out) is False
    assert check_hedging(hedging_out) is True

    # 4. Disagreement Checks
    assert check_disagreement(samples_agree) is False
    assert check_disagreement(samples_disagree) is True

    # 5. Escalation Controller checks & Monotonicity verification
    # Level 0: Always accepts
    esc, reason = should_escalate(empty_out, samples_disagree, strictness=0)
    assert esc is False and "Level 0" in reason
    
    # Level 1: Escalate on empty
    esc, reason = should_escalate(empty_out, samples_agree, strictness=1)
    assert esc is True and "Level 1" in reason
    esc, reason = should_escalate(clean_out, samples_agree, strictness=1)
    assert esc is False and "Level 1 checks passed" in reason

    # Level 2: Escalate on type mismatch
    esc, reason = should_escalate(string_out, samples_agree, strictness=2)
    assert esc is True and "Level 2" in reason
    esc, reason = should_escalate(clean_out, samples_agree, strictness=2)
    assert esc is False

    # Level 3: Escalate on hedging
    esc, reason = should_escalate(hedging_out, samples_agree, strictness=3)
    assert esc is True and "Level 3" in reason
    # Under Level 2, hedging passes!
    esc, _ = should_escalate(hedging_out, samples_agree, strictness=2)
    assert esc is False

    # Level 4: Escalate on sample disagreement
    esc, reason = should_escalate(clean_out, samples_disagree, strictness=4)
    assert esc is True and "Level 4" in reason
    # Under Level 3, disagreement passes!
    esc, _ = should_escalate(clean_out, samples_disagree, strictness=3)
    assert esc is False

    # Level 5: Always escalate
    esc, reason = should_escalate(clean_out, samples_agree, strictness=5)
    assert esc is True and "Level 5" in reason

    print("All verifier smoke tests passed successfully!")
