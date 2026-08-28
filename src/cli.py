"""Unified Command Line Interface for evaluation, live cascade querying, and cache control."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow executing this file directly as a script without PYTHONPATH issues
if __name__ == "__main__" and __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.config import CACHE_PATH, HEADLINE_STRICTNESS
from src.leaderboard import generate_leaderboard
from src.plot import generate_plot
from src.tiers import call_llm, call_slm, sample_slm
from src.verifier import should_escalate


def run_eval() -> None:
    """Run the complete offline strategy evaluation, leaderboard rendering, and plotting pipeline."""
    print("=" * 60)
    print("RUNNING END-TO-END BENCHMARK EVALUATION")
    print("=" * 60)
    
    # 1. Generate metrics and output markdown table + console table
    generate_leaderboard()
    
    # 2. Render plot
    generate_plot()
    
    print("\nEnd-to-End Evaluation complete successfully!")
    print("=" * 60)


def run_query(query: str, strictness: int = HEADLINE_STRICTNESS) -> None:
    """Dynamically route a single query through the SLM-LLM cascade engine."""
    print("=" * 60)
    print("CASCADE QUERY ROUTER")
    print("=" * 60)
    print(f"Query      : '{query}'")
    print(f"Strictness : Level {strictness}")
    print("-" * 60)

    # 1. Execute SLM
    print("Invoking local SLM...")
    slm_res = call_slm(query)
    slm_text = slm_res["answer"]
    
    # 2. Draw consistency samples
    print("Invoking SLM consistency samples...")
    slm_samples_res = sample_slm(query)
    slm_samples = [sample["answer"] for sample in slm_samples_res]
    
    # 3. Check verifier
    escalate, reason = should_escalate(slm_text, slm_samples, strictness)
    
    print("-" * 60)
    print("ROUTING DECISION")
    print("-" * 60)
    print(f"Decision   : {'ESCALATE to Cloud LLM' if escalate else 'ACCEPT Local SLM'}")
    print(f"Reason     : {reason}")
    print(f"SLM Answer : '{slm_text}'")
    
    if escalate:
        print("\nInvoking cloud LLMFallback...")
        llm_res = call_llm(query)
        print("-" * 60)
        print("LLM RESPONSE DETAILS")
        print("-" * 60)
        print(f"Answer     : '{llm_res['answer']}'")
        print(f"Tokens     : In={llm_res['in_tok']}, Out={llm_res['out_tok']}")
        print(f"Cost       : ${llm_res['cost_usd']:.8f} USD")
        print(f"Latency    : {llm_res['latency_s']:.4f} s")
    else:
        print("-" * 60)
        print("SLM RESPONSE DETAILS")
        print("-" * 60)
        print(f"Tokens     : In={slm_res['in_tok']}, Out={slm_res['out_tok']}")
        print(f"Cost       : ${slm_res['cost_usd']:.8f} USD")
        print(f"Latency    : {slm_res['latency_s']:.4f} s")
        
    print("=" * 60)


def clear_cache() -> None:
    """Safely delete the SQLite cache database and its auxiliary files."""
    deleted_any = False
    # Check cache.sqlite, cache.sqlite-wal, cache.sqlite-shm
    for filename in (CACHE_PATH.name, f"{CACHE_PATH.name}-wal", f"{CACHE_PATH.name}-shm"):
        file_to_del = CACHE_PATH.parent / filename
        if file_to_del.exists():
            try:
                file_to_del.unlink()
                print(f"Deleted cache file: {file_to_del.name}")
                deleted_any = True
            except Exception as e:
                print(f"Failed to delete {file_to_del.name}: {e}")
                
    if not deleted_any:
        print("No cache database files found to delete.")
    else:
        print("SQLite cache cleared successfully.")


def main() -> None:
    """CLI Entrypoint parsing command line sub-arguments."""
    parser = argparse.ArgumentParser(
        description="Hybrid SLM+LLM Cascade Router CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Eval command
    subparsers.add_parser("eval", help="Run the full cascade benchmark evaluation")

    # Query command
    query_parser = subparsers.add_parser("query", help="Route a live query through the cascade")
    query_parser.add_argument("text", type=str, help="The query string to evaluate")
    query_parser.add_argument(
        "--strictness", 
        type=int, 
        default=HEADLINE_STRICTNESS,
        choices=[0, 1, 2, 3, 4, 5],
        help="Monotonic verifier strictness level (0 to 5)"
    )

    # Clear-cache command
    subparsers.add_parser("clear-cache", help="Wipe the persistent SQLite cache database")

    args = parser.parse_args()

    if args.command == "eval":
        run_eval()
    elif args.command == "query":
        run_query(args.text, args.strictness)
    elif args.command == "clear-cache":
        clear_cache()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
