"""Diagnostic pass to calibrate performance ceiling (LLM) and floor (SLM)."""

from __future__ import annotations

import sys
from pathlib import Path

# Allow executing this file directly as a script without PYTHONPATH issues
if __name__ == "__main__" and __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.dataset import load_eval_set
from src.grader import extract_answer, grade_answer
from src.tiers import call_llm, call_slm


def run_calibration():
    """Execute evaluation on a 20-query subset and assert LLM accuracy > SLM accuracy."""
    print("=" * 60)
    print("RUNNING CALIBRATION GATE (N=20)")
    print("=" * 60)

    dataset = load_eval_set()
    calibration_set = dataset[:20]

    slm_correct = 0
    llm_correct = 0
    total = len(calibration_set)

    for idx, item in enumerate(calibration_set):
        query = item["query"]
        target = item["target_answer"]
        print(f"[{idx+1}/{total}] Processing query ID {item['id']}...")

        # Invoke SLM
        slm_res = call_slm(query)
        slm_ans = slm_res["answer"]
        slm_extracted = extract_answer(slm_ans)
        slm_is_correct = grade_answer(slm_ans, target)
        if slm_is_correct:
            slm_correct += 1

        # Invoke LLM
        llm_res = call_llm(query)
        llm_ans = llm_res["answer"]
        llm_extracted = extract_answer(llm_ans)
        llm_is_correct = grade_answer(llm_ans, target)
        if llm_is_correct:
            llm_correct += 1

    # Calculate Accuracies
    slm_accuracy = (slm_correct / total) * 100
    llm_accuracy = (llm_correct / total) * 100

    print("-" * 60)
    print("CALIBRATION SUMMARY")
    print("-" * 60)
    print(f"Subset Size  : {total}")
    print(f"SLM Accuracy : {slm_accuracy:.2f}% ({slm_correct}/{total})")
    print(f"LLM Accuracy : {llm_accuracy:.2f}% ({llm_correct}/{total})")
    print("-" * 60)

    # Assert LLM outperforms SLM
    assert llm_accuracy > slm_accuracy, (
        f"Calibration Failed: LLM is not more accurate than SLM. "
        f"SLM: {slm_accuracy:.2f}%, LLM: {llm_accuracy:.2f}%"
    )
    print("Calibration Gate Passed Successfully!")
    print("=" * 60)


if __name__ == "__main__":
    run_calibration()
