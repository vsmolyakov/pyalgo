import collections
import csv
import random
import time
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt


# ============================================================
# 1. CUBE GEOMETRY  (2 x 2 x 2)
# ============================================================

# Corner coordinates.
#
# x = right (+1) / left (-1)
# y = up    (+1) / down (-1)
# z = front (+1) / back (-1)
#
# Corner ordering:
#
#       ULB -------- UBR
#       /              /
#      /              /
#    UFL ----------- URF
#
#    DLF ----------- DFR
#      \              \
#       \              \
#       DBL -------- DRB

CORNERS = [
    ( 1,  1,  1),   # 0 URF  (x, y, z)
    (-1,  1,  1),   # 1 UFL
    (-1,  1, -1),   # 2 ULB
    ( 1,  1, -1),   # 3 UBR
    ( 1, -1,  1),   # 4 DFR
    (-1, -1,  1),   # 5 DLF
    (-1, -1, -1),   # 6 DBL
    ( 1, -1, -1),   # 7 DRB
]


# Face outward normals
FACES = {
    "U": ( 0,  1,  0),
    "D": ( 0, -1,  0),
    "R": ( 1,  0,  0),
    "L": (-1,  0,  0),
    "F": ( 0,  0,  1),
    "B": ( 0,  0, -1),
}


# ------------------------------------------------------------
# Create the 24 sticker positions
# 24 = 8 corners * 3 stickers per corner
# ------------------------------------------------------------

# Each sticker is:
#
#     (corner_index, face, position, normal)

STICKERS = []

for corner_index, position in enumerate(CORNERS):

    for face, normal in FACES.items():

        # A sticker exists on this face if the corner lies
        # directly on that face.
        if sum(
            position[i] * normal[i]
            for i in range(3)
        ) == 1:

            STICKERS.append(
                (
                    corner_index,
                    face,
                    position,
                    normal,
                )
            )


# Map (corner, face) -> sticker index
STICKER_INDEX = {
    (corner, face): i
    for i, (corner, face, position, normal)
    in enumerate(STICKERS)
}


# ============================================================
# 2. ROTATION
# ============================================================

def rotate_vector(v, axis, direction):
    """
    Rotate vector v by +/-90 degrees around axis.

    direction:
        +1 = +90 degrees
        -1 = -90 degrees
    """

    v = np.array(v)
    axis = np.array(axis)

    if direction == 1:

        return tuple(
            np.cross(axis, v)
            + axis * np.dot(axis, v)
        )

    else:

        return tuple(
            -np.cross(axis, v)
            + axis * np.dot(axis, v)
        )


# ============================================================
# 3. GENERATE FACE MOVES
# ============================================================

def create_face_permutation(face):
    """
    Create the permutation corresponding to a clockwise
    quarter-turn of a face.

    permutation[new_position] = old_position
    """

    axis = FACES[face]

    permutation = list(range(24))

    for old_index, (
        corner,
        sticker_face,
        position,
        normal
    ) in enumerate(STICKERS):

        # Is this sticker on the face being turned?
        if sum(
            position[i] * axis[i]
            for i in range(3)
        ) == 1:

            # Clockwise when looking directly at the face.
            new_position = rotate_vector(
                position,
                axis,
                -1
            )

            new_normal = rotate_vector(
                normal,
                axis,
                -1
            )

            new_corner = CORNERS.index(new_position)

            new_face = next(
                f
                for f, n in FACES.items()
                if n == new_normal
            )

            new_index = STICKER_INDEX[
                (new_corner, new_face)
            ]

            permutation[new_index] = old_index

    return tuple(permutation)


# Quarter-turn permutations
QUARTER_MOVES = {
    face: create_face_permutation(face)
    for face in FACES
}


# ============================================================
# 4. APPLY A MOVE
# ============================================================

SOLVED = tuple(range(24))


def apply_move(state, permutation):
    """
    Apply a permutation to a cube state.
    For new position i, look up the old position specified by permutation[i], and copy the sticker from there.
    """

    return tuple(
        state[permutation[i]]
        for i in range(24)
    )


# ============================================================
# 5. CREATE ALL 18 STANDARD MOVES
# ============================================================

# We use:
#
#     U   = clockwise
#     U'  = counter-clockwise
#     U2  = 180 degrees
#
# and similarly for all six faces.

ACTIONS = []


for face in ["U", "D", "R", "L", "F", "B"]:

    quarter = QUARTER_MOVES[face]

    # Clockwise
    ACTIONS.append(
        (face, quarter, face)
    )

    # 180 degrees
    half = apply_move(
        quarter,
        quarter
    )

    ACTIONS.append(
        (face + "2", half, face)
    )

    # Counter-clockwise
    inverse = apply_move(
        half,
        quarter
    )

    ACTIONS.append(
        (face + "'", inverse, face)
    )

# ============================================================
# 6. CORNER PERMUTATION
# ============================================================

def corner_permutation(state):
    """
    Ignore corner orientation and determine which corner cubie
    occupies each corner position.
    
    Simplify the 24-sticker cube representation into an 8-corner representation
    so that we can build a heuristic for IDA*

    IDA* needs a heuristic that answers a simpler question:
    How far is the cube from having all its corner cubies in their correct positions?

    Example:

        (0,1,2,3,4,5,6,7)

    is the solved permutation.
    """

    result = []

    for destination_corner in range(8):

        source_corners = []

        for sticker_position, (
            corner,
            face,
            position,
            normal
        ) in enumerate(STICKERS):

            if corner == destination_corner:

                source_sticker = state[sticker_position]

                source_corner = STICKERS[
                    source_sticker
                ][0]

                source_corners.append(
                    source_corner
                )

        # All 3 stickers must belong to the same cubie.
        assert len(set(source_corners)) == 1

        result.append(source_corners[0])

    return tuple(result)


# ============================================================
# 7. PROJECT EACH MOVE ONTO CORNER PERMUTATION
# ============================================================

CORNER_MOVES = {}

for name, permutation, face in ACTIONS:

    moved_state = apply_move(
        SOLVED,
        permutation
    )

    CORNER_MOVES[name] = corner_permutation(
        moved_state
    )

# ============================================================
# 8. BUILD A PATTERN DATABASE
# ============================================================

"""
The heuristic ignores corner orientation.

It only asks:

    "How many moves are necessary to put all 8 corner
     cubies into their correct positions?"

There are only:

    8! = 40,320

possible corner permutations.

We can calculate the exact distance for every one of them
with BFS.

Because this ignores orientation, it can NEVER overestimate
the real distance.

Therefore it is an admissible IDA* heuristic.
"""


def build_corner_pattern_database():

    solved_permutation = tuple(range(8))

    distance = {
        solved_permutation: 0
    }

    queue = collections.deque(
        [solved_permutation]
    )

    while queue:

        current = queue.popleft()

        current_distance = distance[current]

        for move in CORNER_MOVES.values():

            # new[i] = old[move[i]]
            next_state = tuple(
                current[move[i]]
                for i in range(8)
            )

            if next_state not in distance:

                distance[next_state] = (
                    current_distance + 1
                )

                queue.append(next_state)

    return distance


print("Building heuristic table...")

CORNER_DISTANCE = (
    build_corner_pattern_database()
)

print(
    "Heuristic states:",
    len(CORNER_DISTANCE)
)

# ============================================================
# 9. HEURISTIC
# ============================================================

def heuristic(state):

    permutation = corner_permutation(state)

    return CORNER_DISTANCE[permutation]


# ============================================================
# 10. MOVE PRUNING
# ============================================================

OPPOSITE = {
    "U": "D",
    "D": "U",

    "R": "L",
    "L": "R",

    "F": "B",
    "B": "F",
}


FACE_ORDER = {
    "U": 0,
    "D": 1,
    "R": 2,
    "L": 3,
    "F": 4,
    "B": 5,
}


def should_prune(last_face, current_face):

    if last_face is None:
        return False

    # Never turn the same face twice consecutively.
    #
    # For example:
    #
    #     R R'
    #     U U2
    #
    # can always be represented more efficiently.

    if current_face == last_face:
        return True

    # Opposite faces commute.
    #
    # For example:
    #
    #     U D
    #
    # is equivalent to:
    #
    #     D U
    #
    # We keep only one ordering to avoid searching both.
    if (
        current_face == OPPOSITE[last_face]
        and
        FACE_ORDER[current_face]
        < FACE_ORDER[last_face]
    ):
        return True

    return False


# ============================================================
# 11. IDA*
# ============================================================

class IDAStarSolver:

    def __init__(self):
        self.nodes = 0
        self.path = []
        self.history = []
        self.generated = 0
        self.heuristic_evaluations = 0
        self.pruned_moves = 0
        self.peak_depth = 0
        self.elapsed_seconds = 0.0

    def search(self, state, depth, bound, last_face):
        """Depth-first search for one IDA* threshold iteration."""
        self.nodes += 1
        self.heuristic_evaluations += 1
        self.peak_depth = max(self.peak_depth, depth)

        h = heuristic(state)
        f = depth + h
        if f > bound:
            return f
        if state == SOLVED:
            return True

        minimum = float("inf")
        for name, permutation, face in ACTIONS:
            if should_prune(last_face, face):
                self.pruned_moves += 1
                continue

            self.generated += 1
            next_state = apply_move(state, permutation)
            self.path.append(name)
            result = self.search(next_state, depth + 1, bound, face)
            if result is True:
                return True
            self.path.pop()
            if result < minimum:
                minimum = result
        return minimum

    def solve(self, state, max_depth=11, verbose=True):
        """Solve with IDA*, recording per-threshold and total statistics."""
        self.nodes = 0
        self.path = []
        self.history = []
        self.generated = 0
        self.heuristic_evaluations = 0
        self.pruned_moves = 0
        self.peak_depth = 0
        self.elapsed_seconds = 0.0

        bound = heuristic(state)
        if verbose:
            print(f"Initial heuristic = {bound}")

        overall_start = time.perf_counter()
        while bound <= max_depth:
            iteration_start = time.perf_counter()
            before_nodes = self.nodes
            before_generated = self.generated
            before_evals = self.heuristic_evaluations
            before_pruned = self.pruned_moves
            if verbose:
                print(f"IDA* depth bound = {bound}")

            result = self.search(state, 0, bound, None)
            iteration_seconds = time.perf_counter() - iteration_start
            self.history.append({
                "threshold": bound,
                "nodes": self.nodes - before_nodes,
                "generated": self.generated - before_generated,
                "heuristic_evaluations": self.heuristic_evaluations - before_evals,
                "pruned_moves": self.pruned_moves - before_pruned,
                "seconds": iteration_seconds,
            })

            if result is True:
                self.elapsed_seconds = time.perf_counter() - overall_start
                return self.path.copy()
            if result == float("inf"):
                break
            bound = result

        self.elapsed_seconds = time.perf_counter() - overall_start
        return None


# ============================================================
# 12. SCRAMBLE PARSER
# ============================================================

ACTION_LOOKUP = {
    name: permutation
    for name, permutation, face
    in ACTIONS
}

def scramble_cube(scramble):

    state = SOLVED

    moves = scramble.split()

    for move in moves:

        if move not in ACTION_LOOKUP:

            raise ValueError(
                f"Unknown move: {move}"
            )

        state = apply_move(
            state,
            ACTION_LOOKUP[move]
        )

    return state


# ============================================================
# 13. VERIFY A SOLUTION
# ============================================================

def apply_solution(state, solution):

    for move in solution:

        state = apply_move(
            state,
            ACTION_LOOKUP[move]
        )

    return state


# ============================================================
# 14. PLOTTING AND BENCHMARKING
# ============================================================


def plot_pattern_database(output_dir="ida_plots"):
    """Visualize the corner-permutation PDB's distance distribution."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    distances = np.asarray(list(CORNER_DISTANCE.values()), dtype=int)
    counts = np.bincount(distances)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    axes[0].bar(np.arange(len(counts)), counts, edgecolor="black")
    axes[0].set(title="Corner-permutation PDB: distance histogram",
                xlabel="PDB distance h(s)", ylabel="Number of permutations")
    axes[0].set_xticks(np.arange(len(counts)))
    axes[1].bar(np.arange(len(counts)), counts / len(distances), edgecolor="black")
    axes[1].set(title="Fraction of permutations by PDB distance",
                xlabel="PDB distance h(s)", ylabel="Fraction of all PDB states")
    axes[1].set_xticks(np.arange(len(counts)))
    fig.tight_layout()
    fig.savefig(output_dir / "pdb_distance_distribution.png", dpi=160)
    plt.close(fig)

    # PDB coverage and distance summary are useful for checking the abstraction.
    summary = {
        "pdb_states": int(len(distances)),
        "expected_permutations": 40320,
        "max_distance": int(distances.max()),
        "mean_distance": float(distances.mean()),
        "median_distance": float(np.median(distances)),
    }
    with open(output_dir / "pdb_summary.txt", "w", encoding="utf-8") as f:
        for key, value in summary.items():
            f.write(f"{key}: {value}\n")
    return summary


def plot_single_solve(history, output_dir="ida_plots", label="example"):
    """Plot work performed at each IDA* threshold for one solve."""
    if not history:
        return
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    thresholds = [x["threshold"] for x in history]

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    axes[0].bar(thresholds, [x["nodes"] for x in history], edgecolor="black")
    axes[0].set(title="IDA* nodes expanded per threshold", xlabel="f-cost threshold", ylabel="Nodes expanded")
    axes[0].set_xticks(thresholds)
    axes[1].plot(thresholds, [x["seconds"] for x in history], marker="o")
    axes[1].set(title="Runtime per threshold", xlabel="f-cost threshold", ylabel="Seconds")
    axes[1].set_xticks(thresholds)
    fig.tight_layout()
    fig.savefig(output_dir / f"{label}_threshold_profile.png", dpi=160)
    plt.close(fig)


def make_random_scramble(length, rng):
    """Generate a scramble without consecutive turns of the same face."""
    faces = list(FACES)
    moves_by_face = {face: [a[0] for a in ACTIONS if a[2] == face] for face in faces}
    result = []
    previous_face = None
    for _ in range(length):
        choices = [face for face in faces if face != previous_face]
        face = rng.choice(choices)
        result.append(rng.choice(moves_by_face[face]))
        previous_face = face
    return " ".join(result)


def run_benchmarks(num_scrambles=30, min_length=1, max_length=11,
                   max_depth=11, seed=7, output_dir="ida_plots"):
    """Benchmark random scrambles at several lengths; saves CSV and plots."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    rows = []

    # Balanced coverage: cycle through lengths rather than sampling lengths uniformly.
    for i in range(num_scrambles):
        scramble_length = min_length + (i % (max_length - min_length + 1))
        scramble = make_random_scramble(scramble_length, rng)
        cube = scramble_cube(scramble)
        solver = IDAStarSolver()
        solution = solver.solve(cube, max_depth=max_depth, verbose=False)
        rows.append({
            "scramble": scramble,
            "scramble_length": scramble_length,
            "solution_length": len(solution) if solution is not None else None,
            "solved": solution is not None,
            "nodes": solver.nodes,
            "generated": solver.generated,
            "heuristic_evaluations": solver.heuristic_evaluations,
            "pruned_moves": solver.pruned_moves,
            "peak_depth": solver.peak_depth,
            "seconds": solver.elapsed_seconds,
            "threshold_iterations": len(solver.history),
            "initial_heuristic": heuristic(cube),
        })
        print(f"Benchmark {i + 1:>3}/{num_scrambles}: scramble_len={scramble_length}, "
              f"solution={rows[-1]['solution_length']}, nodes={solver.nodes}, "
              f"time={solver.elapsed_seconds:.4f}s")

    csv_path = output_dir / "ida_benchmark_results.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    solved_rows = [r for r in rows if r["solved"]]
    if solved_rows:
        lengths = sorted(set(r["scramble_length"] for r in solved_rows))
        means_nodes = [np.mean([r["nodes"] for r in solved_rows if r["scramble_length"] == n]) for n in lengths]
        medians_nodes = [np.median([r["nodes"] for r in solved_rows if r["scramble_length"] == n]) for n in lengths]
        means_time = [np.mean([r["seconds"] for r in solved_rows if r["scramble_length"] == n]) for n in lengths]

        fig, axes = plt.subplots(2, 2, figsize=(12, 9))
        axes[0, 0].scatter([r["solution_length"] for r in solved_rows],
                           [r["nodes"] for r in solved_rows], alpha=0.75)
        axes[0, 0].set(title="Search effort vs. solution length", xlabel="Solution length", ylabel="Nodes expanded")
        axes[0, 0].set_yscale("log")

        axes[0, 1].errorbar(lengths, means_nodes, fmt="o-", label="Mean nodes")
        axes[0, 1].plot(lengths, medians_nodes, "s--", label="Median nodes")
        axes[0, 1].set(title="Search effort vs. scramble length", xlabel="Scramble length (moves)", ylabel="Nodes expanded")
        axes[0, 1].set_yscale("log")
        axes[0, 1].legend()

        axes[1, 0].plot(lengths, means_time, "o-")
        axes[1, 0].set(title="Mean runtime vs. scramble length", xlabel="Scramble length (moves)", ylabel="Seconds")

        axes[1, 1].scatter([r["initial_heuristic"] for r in solved_rows],
                           [r["nodes"] for r in solved_rows], alpha=0.75)
        axes[1, 1].set(title="Search effort vs. initial heuristic", xlabel="Initial heuristic h(s)", ylabel="Nodes expanded")
        axes[1, 1].set_yscale("log")
        fig.tight_layout()
        fig.savefig(output_dir / "benchmark_performance.png", dpi=160)
        plt.close(fig)

        # Distribution plots expose variability hidden by averages.
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
        axes[0].hist([r["nodes"] for r in solved_rows], bins=20, edgecolor="black")
        axes[0].set(title="Distribution of nodes expanded", xlabel="Nodes expanded", ylabel="Number of scrambles")
        axes[0].set_xscale("log")
        axes[1].hist([r["seconds"] for r in solved_rows], bins=20, edgecolor="black")
        axes[1].set(title="Distribution of solve times", xlabel="Seconds", ylabel="Number of scrambles")
        fig.tight_layout()
        fig.savefig(output_dir / "benchmark_distributions.png", dpi=160)
        plt.close(fig)

    print(f"Saved benchmark CSV: {csv_path}")
    return rows


# ============================================================
# 15. EXAMPLE
# ============================================================

if __name__ == "__main__":
    OUTPUT_DIR = "ida_plots"
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    print("\\nBuilding PDB plots...")
    print(plot_pattern_database(OUTPUT_DIR))

    scramble = "R U R2 F D F2 U"
    print("\\nExample scramble:")
    print(scramble)
    cube = scramble_cube(scramble)
    solver = IDAStarSolver()
    solution = solver.solve(cube, max_depth=11)

    print("\\nSolution:", " ".join(solution) if solution is not None else "not found within max_depth")
    print("Solution length:", len(solution) if solution is not None else None)
    print("Nodes expanded:", solver.nodes)
    print("Nodes generated:", solver.generated)
    print("Heuristic evaluations:", solver.heuristic_evaluations)
    print("Moves pruned:", solver.pruned_moves)
    print("Peak search depth:", solver.peak_depth)
    print(f"Elapsed seconds: {solver.elapsed_seconds:.6f}")
    print("Threshold history:", solver.history)

    if solution is not None:
        final_state = apply_solution(cube, solution)
        print("Solution verified:", final_state == SOLVED)
    plot_single_solve(solver.history, OUTPUT_DIR, label="example")

    run_benchmarks(num_scrambles=9, min_length=1, max_length=11,
                   max_depth=11, seed=7, output_dir=OUTPUT_DIR)
    print(f"\nPlots and CSV saved in ./{OUTPUT_DIR}/")
