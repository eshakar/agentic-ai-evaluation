"""Run an evaluation from the command line without starting the API server.

Usage:
    python -m scripts.run_eval --agent echo --dataset sample_eval.jsonl
    python -m scripts.run_eval --agent claude --evaluators contains tool_sequence llm_judge
"""

import argparse
import asyncio

from app.core.logging import setup_logging
from app.services.evaluation_service import load_dataset, run_evaluation


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an agent evaluation.")
    parser.add_argument("--agent", default="echo")
    parser.add_argument("--dataset", default="sample_eval.jsonl")
    parser.add_argument(
        "--evaluators", nargs="+", default=["contains", "tool_sequence", "latency", "no_error"]
    )
    args = parser.parse_args()

    setup_logging()
    cases = load_dataset(args.dataset)
    summary = asyncio.run(run_evaluation(args.agent, cases, args.evaluators))

    print(f"\nRun {summary.run_id}  agent={summary.agent}  cases={summary.num_cases}")
    print(f"Pass rate: {summary.pass_rate:.0%}   mean latency: {summary.mean_latency_ms:.0f}ms")
    for metric, score in summary.mean_scores.items():
        print(f"  {metric:<15} {score:.3f}")
    print("\nFailures:")
    for r in summary.results:
        for m in r.metrics:
            if not m.passed:
                print(f"  [{r.case_id}] {m.name}: {m.reason}")
    print(f"\nFull report: results/{summary.run_id}.json")


if __name__ == "__main__":
    main()
