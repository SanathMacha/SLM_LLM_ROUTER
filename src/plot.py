"""Generate and export the hybrid router evaluation deferral curve plot."""

from __future__ import annotations

import sys
from pathlib import Path

# Allow executing this file directly as a script without PYTHONPATH issues
if __name__ == "__main__" and __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt
import numpy as np

from src.config import CURVE_PATH, HEADLINE_STRICTNESS
from src.stats import calculate_metrics


def generate_plot() -> None:
    """Plot accuracy vs escalation rate comparing the Cascade Router against baselines and export to CURVE_PATH."""
    metrics = calculate_metrics()
    strategies = metrics["strategies"]
    
    # Sort strategies by routing rate to plot clean connected lines
    sorted_strats = sorted(strategies, key=lambda x: x["routing_rate"])
    
    # Extract points
    x_cascade = [s["routing_rate"] for s in sorted_strats]
    y_cascade = [s["cascade"]["accuracy"] for s in sorted_strats]
    
    x_random = [s["routing_rate"] for s in sorted_strats]
    y_random = [s["random"]["accuracy"] for s in sorted_strats]
    
    x_oracle = [s["routing_rate"] for s in sorted_strats]
    y_oracle = [s["oracle"]["accuracy"] for s in sorted_strats]
    
    # Set styling
    plt.figure(figsize=(9, 6))
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    
    # Plot lines
    plt.plot(x_random, y_random, label="Random Router (Diagonal Baseline)", color="red", linestyle="--", alpha=0.7)
    plt.plot(x_oracle, y_oracle, label="Oracle Router (Ceiling Baseline)", color="green", linestyle="-.", alpha=0.7)
    plt.plot(x_cascade, y_cascade, label="Cascade Router (Empirical)", color="blue", marker="o", linewidth=2.5)
    
    # Highlight points and annotations
    for s in sorted_strats:
        strictness = s["strictness"]
        is_headline = (strictness == HEADLINE_STRICTNESS)
        
        # Point label
        label_text = f"L{strictness}"
        if is_headline:
            label_text += " (Headline)"
            
        plt.annotate(
            label_text,
            (s["routing_rate"], s["cascade"]["accuracy"]),
            textcoords="offset points",
            xytext=(10, -5 if strictness == 0 else 5),
            ha="left",
            weight="bold" if is_headline else "normal",
            color="darkblue" if is_headline else "black"
        )
        
        # Highlight Headline operating point specifically
        if is_headline:
            plt.scatter(
                s["routing_rate"], 
                s["cascade"]["accuracy"], 
                color="orange", 
                edgecolors="blue", 
                s=120, 
                zorder=5, 
                label="Headline Operating Point"
            )

    # Format chart
    plt.title("Routing Engine Deferral Curve", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Escalation / Deferral Rate (f)", fontsize=11)
    plt.ylabel("Accuracy", fontsize=11)
    plt.xlim(-0.05, 1.05)
    plt.ylim(-0.05, 1.05)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(loc="lower right", frameon=True, facecolor="white", edgecolor="lightgray")
    
    # Save PNG
    CURVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(CURVE_PATH, dpi=300)
    plt.close()
    
    print(f"Deferral curve chart generated and saved successfully to {CURVE_PATH.resolve()}")


if __name__ == "__main__":
    generate_plot()
