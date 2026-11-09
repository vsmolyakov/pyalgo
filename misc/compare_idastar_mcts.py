"""
Compare the IDA* and MCTS 2x2x2 Rubik's Cube solvers on identical scrambles.

Place this file in the same directory as:
    rubiks_cube_analysis.py
    rubiks_cube_mcts.py

Run:
    python compare_idastar_mcts.py

The benchmark generates each scramble once, constructs the same cube state for
both implementations, and gives each solver that exact state. Results are saved
to comparison_results/comparison.csv and comparison_plots.png.

Notes:
- IDA* is depth-bounded by --ida-max-depth; its implementation has no time-limit
  parameter, so choose conservative scramble depths for practical runtimes.
- MCTS is bounded by --mcts-time-limit and --mcts-iterations.
- Search-node counts are algorithm-specific and should not be interpreted as
  directly equivalent units of work.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import math
import random
import statistics
import sys
import time
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def load_module(module_name: str, file_path: Path):
    """Import a Python file by path (supports the parentheses in its filename)."""
    if not file_path.exists():
        raise FileNotFoundError(
            f"Could not find {file_path.name}. Put it beside {Path(__file__).name}."
        )
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot import {file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def build_common_scrambles(ida, count, min_depth, max_depth, seed):
    """Generate a reproducible, balanced set of scrambles using IDA*'s move set."""
    rng = random.Random(seed)
    cases = []
    for index in range(count):
        depth = min_depth + index % (max_depth - min_depth + 1)
        scramble = ida.make_random_scramble(depth, rng)
        state = ida.scramble_cube(scramble)
        cases.append({
            "case_id": index + 1,
            "scramble_depth": depth,
            "scramble": scramble,
            "state": state,
        })
    return cases


def run_idastar(ida, state, max_depth):
    solver = ida.IDAStarSolver()
    solution = solver.solve(state, max_depth=max_depth, verbose=False)
    verified = solution is not None and ida.apply_solution(state, solution) == ida.SOLVED
    return {
        "solved": bool(verified),
        "solution": solution if verified else None,
        "solution_length": len(solution) if verified else None,
        "elapsed_seconds": solver.elapsed_seconds,
        "nodes": solver.nodes,
        "generated": solver.generated,
        "heuristic_evaluations": solver.heuristic_evaluations,
        "pruned_moves": solver.pruned_moves,
        "peak_depth": solver.peak_depth,
        "iterations": len(solver.history),
        "iterations_to_solution": None,
        "rollout_steps": None,
    }


def run_mcts(mcts, state, iterations, time_limit, rollout_depth, seed):
    solver = mcts.MCTSCubeSolver(
        solved=mcts.SOLVED,
        actions=mcts.ACTIONS,
        apply_move=mcts.apply_move,
        exploration=math.sqrt(2),
        rollout_depth=rollout_depth,
        seed=seed,
    )
    solution = solver.solve(
        state,
        iterations=iterations,
        time_limit=time_limit,
    )
    verified = (
        solution is not None
        and solver.verify_solution(state, solution)
    )
    stats = solver.stats
    return {
        "solved": bool(verified),
        "solution": solution if verified else None,
        "solution_length": len(solution) if verified else None,
        "elapsed_seconds": stats["elapsed_seconds"],
        "nodes": stats["expanded_nodes"],
        "generated": stats["expanded_nodes"],
        "heuristic_evaluations": None,
        "pruned_moves": None,
        "peak_depth": stats["max_tree_depth"],
        "iterations": stats["iterations"],
        "iterations_to_solution": stats["iterations_to_solution"],
        "rollout_steps": stats["rollout_steps"],
    }


def assert_implementations_agree(ida, mcts, scramble):
    """Guard against comparing different move conventions or cube states."""
    ida_state = ida.scramble_cube(scramble)
    mcts_moves = scramble.split()
    mcts_state = mcts.apply_moves(
        mcts.SOLVED, mcts_moves, mcts.ACTIONS, mcts.apply_move
    )
    if ida_state != mcts_state:
        raise RuntimeError(
            "The two modules produced different states for the same scramble: "
            f"{scramble}"
        )
    if ida.SOLVED != mcts.SOLVED:
        raise RuntimeError("The two modules use different solved-state encodings.")


def save_csv(rows, path):
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def print_summary(rows):
    print("\nAggregate comparison by scramble depth")
    print(
        f"{'Depth':>5} {'Solver':>8} {'Success':>9} "
        f"{'Mean time':>12} {'Mean length':>13} {'Mean nodes':>13}"
    )
    depths = sorted({row["scramble_depth"] for row in rows})
    for depth in depths:
        group = [r for r in rows if r["scramble_depth"] == depth]
        for solver_name in ("IDA*", "MCTS"):
            subset = [r for r in group if r["solver"] == solver_name]
            successes = [r for r in subset if r["solved"]]
            success_rate = len(successes) / len(subset) if subset else 0.0
            mean_time = statistics.mean(r["elapsed_seconds"] for r in subset)
            lengths = [r["solution_length"] for r in successes]
            nodes = [r["nodes"] for r in subset]
            mean_length = statistics.mean(lengths) if lengths else float("nan")
            mean_nodes = statistics.mean(nodes) if nodes else float("nan")
            print(
                f"{depth:5d} {solver_name:>8} {success_rate:8.1%} "
                f"{mean_time:11.4f}s {mean_length:13.2f} {mean_nodes:13.1f}"
            )


def create_plots(rows, output_path):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib is not installed; skipping plots.")
        return

    depths = sorted({r["scramble_depth"] for r in rows})
    metrics = [
        ("success_rate", "Success rate", "Fraction"),
        ("elapsed_seconds", "Mean runtime", "Seconds"),
        ("solution_length", "Mean solution length (solved cases)", "Moves"),
        ("nodes", "Mean algorithm-specific node count", "Nodes"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for ax, (metric, title, ylabel) in zip(axes.flat, metrics):
        for solver_name in ("IDA*", "MCTS"):
            values = []
            for depth in depths:
                group = [
                    r for r in rows
                    if r["scramble_depth"] == depth
                    and r["solver"] == solver_name
                ]
                if metric == "success_rate":
                    value = (
                        sum(bool(r["solved"]) for r in group) / len(group)
                        if group else float("nan")
                    )
                else:
                    eligible = [
                        r[metric] for r in group
                        if r[metric] is not None
                        and (metric != "solution_length" or r["solved"])
                    ]
                    value = statistics.mean(eligible) if eligible else float("nan")
                values.append(value)
            ax.plot(depths, values, marker="o", label=solver_name)
        ax.set_title(title)
        ax.set_xlabel("Generated scramble length (moves)")
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3)
        ax.legend()
        if metric == "success_rate":
            ax.set_ylim(0, 1.05)
    fig.suptitle("2x2x2 Rubik's Cube: IDA* vs MCTS")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def benchmark(args):
    ida = load_module("rubiks_cube_analysis", BASE_DIR / "rubiks_cube_analysis.py")
    mcts = load_module("rubik_cube_mcts", BASE_DIR / "rubiks_cube_mcts.py")

    # Check the duplicated cube implementations before running any experiments.
    assert_implementations_agree(ida, mcts, "R U F2 D'")

    cases = build_common_scrambles(
        ida, args.cases, args.min_depth, args.max_depth, args.seed
    )
    output_dir = BASE_DIR / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for case in cases:
        scramble = case["scramble"]
        state = case["state"]
        assert_implementations_agree(ida, mcts, scramble)

        print(
            f"\nCase {case['case_id']}/{len(cases)} | "
            f"depth={case['scramble_depth']} | {scramble}"
        )

        # Run sequentially on the same immutable starting state.
        ida_result = run_idastar(ida, state, args.ida_max_depth)
        mcts_result = run_mcts(
            mcts, state,
            args.mcts_iterations,
            args.mcts_time_limit,
            args.rollout_depth,
            args.seed + case["case_id"],
        )

        for solver_name, result in (("IDA*", ida_result), ("MCTS", mcts_result)):
            row = {
                "case_id": case["case_id"],
                "scramble_depth": case["scramble_depth"],
                "scramble": scramble,
                "solver": solver_name,
                **{k: v for k, v in result.items() if k != "solution"},
                "solution": (
                    " ".join(result["solution"])
                    if result["solution"] is not None else None
                ),
            }
            rows.append(row)
            print(
                f"  {solver_name:5s}: solved={result['solved']!s:5s}, "
                f"time={result['elapsed_seconds']:.4f}s, "
                f"solution_length={result['solution_length']}, "
                f"nodes={result['nodes']}"
            )

    csv_path = output_dir / "comparison.csv"
    plot_path = output_dir / "comparison_plots.png"
    save_csv(rows, csv_path)
    print_summary(rows)
    create_plots(rows, plot_path)
    print(f"\nCSV:   {csv_path}")
    print(f"Plots: {plot_path}")
    return rows


def parse_args():
    parser = argparse.ArgumentParser(
        description="Benchmark IDA* and MCTS on identical 2x2x2 cube scrambles."
    )
    parser.add_argument("--cases", type=int, default=15,
                        help="Number of common scrambles (default: 15).")
    parser.add_argument("--min-depth", type=int, default=1)
    parser.add_argument("--max-depth", type=int, default=7)
    parser.add_argument("--ida-max-depth", type=int, default=11)
    parser.add_argument("--mcts-iterations", type=int, default=50000)
    parser.add_argument("--mcts-time-limit", type=float, default=2.0)
    parser.add_argument("--rollout-depth", type=int, default=20)
    parser.add_argument("--seed", type=int, default=1234)
    parser.add_argument("--output-dir", default="comparison_results")
    args = parser.parse_args()
    if args.cases < 1:
        parser.error("--cases must be at least 1")
    if args.min_depth < 0 or args.max_depth < args.min_depth:
        parser.error("Require 0 <= --min-depth <= --max-depth")
    if args.ida_max_depth < 0:
        parser.error("--ida-max-depth must be nonnegative")
    if args.mcts_time_limit <= 0 or args.mcts_iterations < 1:
        parser.error("MCTS time limit and iteration count must be positive")
    return args


if __name__ == "__main__":
    benchmark(parse_args())
