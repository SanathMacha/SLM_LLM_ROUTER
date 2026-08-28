"""Statistics calculations module, computing cost efficiencies, savings, and binomial confidence intervals."""

from __future__ import annotations

import sys
from pathlib import Path

# Allow executing this file directly as a script without PYTHONPATH issues
if __name__ == "__main__" and __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parent.parent))

import numpy as np
from src.strategies import get_routing_strategies


def binomial_confidence_interval(successes: float, trials: int) -> tuple[float, float]:
    """Calculate the Wald 95% binomial confidence interval for a given success count and trial size."""
    if trials == 0:
        return 0.0, 0.0
    p = successes / trials
    # Z-score for 95% confidence is 1.96
    z = 1.96
    se = np.sqrt(max(0.0, p * (1.0 - p) / trials))
    margin = z * se
    lower = max(0.0, p - margin)
    upper = min(1.0, p + margin)
    return lower, upper


def calculate_metrics() -> dict:
    """Analyze all strategies, calculating savings, efficiency, and confidence bounds."""
    raw_data = get_routing_strategies()
    all_llm_cost = raw_data["all_llm_cost"]
    all_llm_accuracy = raw_data["all_llm_accuracy"]
    strategies = raw_data["strategies"]
    
    # We evaluate over 120 queries
    N = 120
    
    processed_strategies = []
    
    for s in strategies:
        strictness = s["strictness"]
        r_rate = s["routing_rate"]
        
        # Cascade metrics
        cascade_acc = s["cascade"]["accuracy"]
        cascade_cost = s["cascade"]["total_cost"]
        
        # Calculate savings percentage vs All-LLM Baseline
        # Savings = 1 - (Total Cascade Cost / All-LLM Cost)
        # Avoid division by zero
        savings_pct = 1.0 - (cascade_cost / all_llm_cost) if all_llm_cost > 0 else 0.0
        
        # Cost per correct answer = total cost / (accuracy * N)
        correct_count = cascade_acc * N
        cost_per_correct = cascade_cost / correct_count if correct_count > 0 else 0.0
        
        # Confidence intervals
        acc_lower, acc_upper = binomial_confidence_interval(correct_count, N)
        rt_lower, rt_upper = binomial_confidence_interval(r_rate * N, N)
        
        processed_strategies.append({
            "strictness": strictness,
            "routing_rate": r_rate,
            "routing_rate_ci": (rt_lower, rt_upper),
            "cascade": {
                "accuracy": cascade_acc,
                "accuracy_ci": (acc_lower, acc_upper),
                "total_cost": cascade_cost,
                "savings_pct": savings_pct,
                "cost_per_correct": cost_per_correct
            },
            "random": {
                "accuracy": s["random"]["accuracy"],
                "total_cost": s["random"]["total_cost"]
            },
            "oracle": {
                "accuracy": s["oracle"]["accuracy"],
                "total_cost": s["oracle"]["total_cost"]
            }
        })
        
    return {
        "all_llm_cost": all_llm_cost,
        "all_llm_accuracy": all_llm_accuracy,
        "strategies": processed_strategies
    }


if __name__ == "__main__":
    print("Running stats smoke test...")
    try:
        metrics = calculate_metrics()
        print(f"All-LLM cost: ${metrics['all_llm_cost']:.4f}")
        for s in metrics["strategies"]:
            cascade = s["cascade"]
            print(f"Level {s['strictness']}: Routing={s['routing_rate']*100:.1f}% "
                  f"(CI: {s['routing_rate_ci'][0]*100:.1f}-{s['routing_rate_ci'][1]*100:.1f}%), "
                  f"Acc={cascade['accuracy']*100:.1f}% "
                  f"(CI: {cascade['accuracy_ci'][0]*100:.1f}-{cascade['accuracy_ci'][1]*100:.1f}%), "
                  f"Cost=${cascade['total_cost']:.4f}, Savings={cascade['savings_pct']*100:.1f}%, "
                  f"Cost/Correct=${cascade['cost_per_correct']:.6f}")
        print("Stats computation pipeline verified successfully!")
    except Exception as e:
        print(f"Stats calculation failed: {e}")
        sys.exit(1)
