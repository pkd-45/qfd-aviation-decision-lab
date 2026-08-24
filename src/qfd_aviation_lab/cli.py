from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import run_demo


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the synthetic aviation decision-support demo."
    )
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--budget", type=float, default=24.0, help="Synthetic fiscal budget units.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    summary = run_demo(args.output_dir, budget_units=args.budget)
    print("\nQFD aviation decision-support synthetic demo")
    print(summary.to_string(index=False))
    print(f"\nOutputs: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
