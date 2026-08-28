"""Replay simulation engine that routes the answer matrix across strictness levels and calculates control baselines."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

# Allow executing this file directly as a script without PYTHONPATH issues
if __name__ == "__main__" and __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.config import RESULTS_PATH
from src.verifier import should_escalate


def load_results() -> list[dict]:
    """Load results matrix from RESULTS_PATH."""
    if not RESULTS_PATH.exists():
        raise FileNotFoundError(f"Results matrix not found at {RESULTS_PATH}. Run src/matrix.py first.")
    with open(RESULTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def simulate_cascade(results: list[dict], strictness: int) -> dict:
    """Simulate routing for a specific strictness level on the pre-computed matrix."""
    escalated_count = 0
    correct_count = 0
    total_cost = 0.0
    N = len(results)

    for item in results:
        slm_text = item["slm_response"]["answer"]
        slm_samples = item["slm_samples"]
        
        # Determine escalation
        escalate, _ = should_escalate(slm_text, slm_samples, strictness)
        
        slm_cost = item["slm_response"]["cost_usd"]
        llm_cost = item["llm_response"]["cost_usd"]

        if escalate:
            escalated_count += 1
            # Double-billed: pay SLM penalty + cloud LLM cost
            total_cost += slm_cost + llm_cost
            if item["llm_correct"]:
                correct_count += 1
        else:
            total_cost += slm_cost
            if item["slm_correct"]:
                correct_count += 1

    routing_rate = escalated_count / N
    accuracy = correct_count / N

    return {
        "strictness": strictness,
        "routing_rate": routing_rate,
        "accuracy": accuracy,
        "total_cost": total_cost,
        "escalated_count": escalated_count
    }


def simulate_random_router(results: list[dict], routing_rate: float, trials: int = 1000) -> dict:
    """Simulate a Random Router control stochastically escalating queries with probability = routing_rate."""
    N = len(results)
    if N == 0:
        return {"accuracy": 0.0, "total_cost": 0.0}

    total_accuracy = 0.0
    total_cost = 0.0

    # We run multiple stochastic trials to get the expected accuracy
    for _ in range(trials):
        trial_correct = 0
        for item in results:
            # Decide randomly based on the routing rate
            if random.random() < routing_rate:
                # Escalated
                total_cost += item["slm_response"]["cost_usd"] + item["llm_response"]["cost_usd"]
                if item["llm_correct"]:
                    trial_correct += 1
            else:
                # Local SLM
                total_cost += item["slm_response"]["cost_usd"]
                if item["slm_correct"]:
                    trial_correct += 1
        total_accuracy += (trial_correct / N)

    # Average over trials
    avg_accuracy = total_accuracy / trials
    avg_cost = total_cost / trials

    return {
        "accuracy": avg_accuracy,
        "total_cost": avg_cost
    }


def simulate_oracle_router(results: list[dict], escalated_budget: int) -> dict:
    """Simulate Oracle Router control escalating strictly the items where SLM is incorrect, up to budget."""
    N = len(results)
    if N == 0:
        return {"accuracy": 0.0, "total_cost": 0.0}

    # Sort items: prioritize queries where SLM is incorrect (slm_correct is False)
    # The Oracle knows exactly which ones are wrong and corrects them first.
    sorted_items = sorted(results, key=lambda x: x["slm_correct"])

    correct_count = 0
    total_cost = 0.0

    for idx, item in enumerate(sorted_items):
        slm_cost = item["slm_response"]["cost_usd"]
        llm_cost = item["llm_response"]["cost_usd"]

        # Escalate up to budget
        if idx < escalated_budget:
            # Escalated
            total_cost += slm_cost + llm_cost
            if item["llm_correct"]:
                correct_count += 1
        else:
            # Local SLM
            total_cost += slm_cost
            if item["slm_correct"]:
                correct_count += 1

    return {
        "accuracy": correct_count / N,
        "total_cost": total_cost
    }


def get_routing_strategies() -> dict:
    """Generate all routing strategies and control baselines across strictness levels 0 to 5."""
    results = load_results()
    
    cascade_runs = []
    for strictness in range(6):
        cascade_runs.append(simulate_cascade(results, strictness))
        
    strategies = []
    for run in cascade_runs:
        r_rate = run["routing_rate"]
        e_budget = run["escalated_count"]
        
        # Run controls
        random_control = simulate_random_router(results, r_rate)
        oracle_control = simulate_oracle_router(results, e_budget)
        
        strategies.append({
            "strictness": run["strictness"],
            "routing_rate": r_rate,
            "cascade": {
                "accuracy": run["accuracy"],
                "total_cost": run["total_cost"]
            },
            "random": {
                "accuracy": random_control["accuracy"],
                "total_cost": random_control["total_cost"]
            },
            "oracle": {
                "accuracy": oracle_control["accuracy"],
                "total_cost": oracle_control["total_cost"]
            }
        })
        
    return {
        "all_llm_cost": sum(item["llm_response"]["cost_usd"] for item in results),
        "all_llm_accuracy": sum(1 if item["llm_correct"] else 0 for item in results) / len(results),
        "strategies": strategies
    }


if __name__ == "__main__":
    print("Running strategies smoke test...")
    try:
        data = get_routing_strategies()
        print(f"Loaded All-LLM Baseline Accuracy: {data['all_llm_accuracy'] * 100:.2f}%")
        print(f"Loaded All-LLM Baseline Cost: ${data['all_llm_cost']:.4f}")
        for s in data["strategies"]:
            print(f"Level {s['strictness']}: Routing={s['routing_rate']*100:.1f}%, "
                  f"Cascade Acc={s['cascade']['accuracy']*100:.1f}%, "
                  f"Random Acc={s['random']['accuracy']*100:.1f}%, "
                  f"Oracle Acc={s['oracle']['accuracy']*100:.1f}%")
        print("Strategies engine loaded and simulated successfully!")
    except Exception as e:
        print(f"Simulation failed: {e}")
        sys.exit(1)
