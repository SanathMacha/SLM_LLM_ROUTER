"""Format and render hybrid routing evaluation stats into a terminal table and export output/leaderboard.md."""

from __future__ import annotations

import sys
from pathlib import Path

# Allow executing this file directly as a script without PYTHONPATH issues
if __name__ == "__main__" and __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.table import Table

from src.config import HEADLINE_STRICTNESS, LEADERBOARD_PATH
from src.stats import calculate_metrics


def generate_leaderboard() -> None:
    """Format evaluation stats into a terminal Table and export a Markdown table to LEADERBOARD_PATH."""
    metrics = calculate_metrics()
    strategies = metrics["strategies"]
    
    console = Console()
    
    # 1. Generate Terminal Table using Rich
    table = Table(title="SLM+LLM Cascade Router Leaderboard (N=120)")
    table.add_column("Strategy/Strictness", justify="left")
    table.add_column("Escalation Rate % (95% CI)", justify="center")
    table.add_column("Accuracy % (95% CI)", justify="center")
    table.add_column("Total Cost USD", justify="right")
    table.add_column("Savings vs LLM %", justify="right")
    table.add_column("Cost / Correct USD", justify="right")

    # Add All-LLM baseline first
    all_llm_cost = metrics["all_llm_cost"]
    all_llm_acc = metrics["all_llm_accuracy"]
    table.add_row(
        "All-LLM Baseline (Ceiling)",
        "100.0% (N/A)",
        f"{all_llm_acc * 100:.1f}% (N/A)",
        f"${all_llm_cost:.4f}",
        "0.0%",
        f"${all_llm_cost / (all_llm_acc * 120):.6f}",
        style="dim"
    )
    
    for s in strategies:
        strictness = s["strictness"]
        rt_rate = s["routing_rate"] * 100
        rt_ci = s["routing_rate_ci"]
        rt_str = f"{rt_rate:.1f}% ({rt_ci[0]*100:.1f}-{rt_ci[1]*100:.1f}%)"
        
        cascade = s["cascade"]
        acc = cascade["accuracy"] * 100
        acc_ci = cascade["accuracy_ci"]
        acc_str = f"{acc:.1f}% ({acc_ci[0]*100:.1f}-{acc_ci[1]*100:.1f}%)"
        
        cost_str = f"${cascade['total_cost']:.4f}"
        savings = f"{cascade['savings_pct'] * 100:.1f}%"
        cost_per_correct = f"${cascade['cost_per_correct']:.6f}"
        
        # Highlight the headline strictness operating point
        is_headline = (strictness == HEADLINE_STRICTNESS)
        row_style = "bold cyan" if is_headline else ""
        label = f"Cascade Router L{strictness}"
        if is_headline:
            label += " [HEADLINE]"
            
        table.add_row(
            label,
            rt_str,
            acc_str,
            cost_str,
            savings,
            cost_per_correct,
            style=row_style
        )
        
    console.print("\n")
    console.print(table)
    console.print("\n")

    # 2. Export Markdown Table to LEADERBOARD_PATH
    LEADERBOARD_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    md_lines = [
        "# SLM+LLM Cascade Router Evaluation Leaderboard",
        "",
        "This table compares our Cascade Router strategies across all strictness thresholds "
        "against the mathematical baseline ceiling (All-LLM).",
        "",
        "| Strategy / Strictness | Escalation Rate (95% CI) | Accuracy (95% CI) | Total Cost (USD) | Savings vs LLM | Cost/Correct (USD) |",
        "| :--- | :---: | :---: | :---: | :---: | :---: |",
        f"| All-LLM Baseline (Ceiling) | 100.0% (N/A) | {all_llm_acc * 100:.1f}% (N/A) | ${all_llm_cost:.4f} | 0.0% | ${all_llm_cost / (all_llm_acc * 120):.6f} |"
    ]
    
    for s in strategies:
        strictness = s["strictness"]
        rt_rate = s["routing_rate"] * 100
        rt_ci = s["routing_rate_ci"]
        rt_str = f"{rt_rate:.1f}% ({rt_ci[0]*100:.1f}%-{rt_ci[1]*100:.1f}%)"
        
        cascade = s["cascade"]
        acc = cascade["accuracy"] * 100
        acc_ci = cascade["accuracy_ci"]
        acc_str = f"{acc:.1f}% ({acc_ci[0]*100:.1f}%-{acc_ci[1]*100:.1f}%)"
        
        cost_str = f"${cascade['total_cost']:.4f}"
        savings = f"{cascade['savings_pct'] * 100:.1f}%"
        cost_per_correct = f"${cascade['cost_per_correct']:.6f}"
        
        label = f"Cascade Router L{strictness}"
        if strictness == HEADLINE_STRICTNESS:
            label = f"**{label} (Headline)**"
            rt_str = f"**{rt_str}**"
            acc_str = f"**{acc_str}**"
            cost_str = f"**{cost_str}**"
            savings = f"**{savings}**"
            cost_per_correct = f"**{cost_per_correct}**"
            
        md_lines.append(f"| {label} | {rt_str} | {acc_str} | {cost_str} | {savings} | {cost_per_correct} |")
        
    with open(LEADERBOARD_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")
        
    print(f"Leaderboard exported successfully to {LEADERBOARD_PATH.resolve()}")


if __name__ == "__main__":
    generate_leaderboard()
