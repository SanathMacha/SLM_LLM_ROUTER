"""Execution pipeline to generate the full evaluation result matrix across the dataset."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# Allow executing this file directly as a script without PYTHONPATH issues
if __name__ == "__main__" and __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.config import RESULTS_PATH
from src.dataset import load_eval_set
from src.grader import grade_answer
from src.tiers import call_llm, call_slm, sample_slm


def build_matrix():
    """Execute SLM, LLM, and consistency samples for all 120 queries, grade, and serialize results."""
    print("=" * 60)
    print("BUILDING MATRIX ENGINE (N=120)")
    print("=" * 60)

    dataset = load_eval_set()
    total = len(dataset)
    results_matrix = []

    for idx, item in enumerate(dataset):
        query = item["query"]
        target = item["target_answer"]
        
        # Execute model queries
        slm_response = call_slm(query)
        slm_samples_res = sample_slm(query)
        llm_response = call_llm(query)
        
        # Extract the raw answer strings from consistency samples for verifier compatibility
        slm_samples = [sample["answer"] for sample in slm_samples_res]
        
        # Grade predictions
        slm_correct = grade_answer(slm_response["answer"], target)
        llm_correct = grade_answer(llm_response["answer"], target)
        
        # Build record
        record = {
            "id": item["id"],
            "query": query,
            "target_answer": target,
            "slm_response": slm_response,
            "slm_samples": slm_samples,
            "slm_correct": slm_correct,
            "llm_response": llm_response,
            "llm_correct": llm_correct
        }
        
        results_matrix.append(record)
        print(f"[{idx+1}/{total}] Processed query ID {item['id']} "
              f"(SLM: {'Correct' if slm_correct else 'Incorrect'}, "
              f"LLM: {'Correct' if llm_correct else 'Incorrect'})")

    # Serialize results to RESULTS_PATH
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results_matrix, f, indent=2)
        
    print("-" * 60)
    print(f"Matrix generation complete. Saved results to {RESULTS_PATH.resolve()}")
    print("=" * 60)


if __name__ == "__main__":
    build_matrix()
