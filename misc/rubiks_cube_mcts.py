import math
import random
import time
import numpy as np
from dataclasses import dataclass, field

import csv
import os
import statistics
import matplotlib.pyplot as plt


@dataclass
class MCTSNode:
    state: tuple
    parent: object = None
    move: str = None
    face: str = None
    children: list = field(default_factory=list)
    untried_actions: list = field(default_factory=list)
    visits: int = 0
    reward: float = 0.0

    @property
    def mean_reward(self):
        return self.reward / self.visits if self.visits else 0.0


class MCTSCubeSolver:
    def __init__(
        self,
        solved,
        actions,
        apply_move,
        exploration=math.sqrt(2),
        rollout_depth=20,
        seed=None,
        history_interval=100,
    ):
        self.solved = solved
        self.actions = list(actions)
        self.apply_move = apply_move
        self.exploration = exploration
        self.rollout_depth = rollout_depth
        self.rng = random.Random(seed)
        self.history_interval = history_interval

        self.stats = {}
        self.history = []
        self.last_root = None

        # Precompute the three sticker positions belonging to each corner.
        # The state stores sticker IDs, and STICKERS[sticker_id][0] gives
        # the corner cubie from which that sticker originated.
        self.corner_positions = [
            tuple(i for i, sticker in enumerate(STICKERS)
                  if sticker[0] == corner_id)
            for corner_id in range(8)
        ]
        self.sticker_source_corner = tuple(
            sticker[0] for sticker in STICKERS
        )

    def is_solved(self, state):
        return state == self.solved

    def heuristic(self, state):
        """
        Return a normalized corner-aware estimate in [0, 1].

        A 2x2x2 cube has eight corner cubies, each represented by three
        stickers. The previous sticker-only score treated every sticker
        independently and could give a misleadingly high score when the
        three stickers of a corner belonged to different cubies.

        Components:
          * 40%: corner cubies in their correct locations (orientation ignored)
          * 30%: stickers in their exact solved positions
          * 30%: completely solved corners (piece and orientation correct)

        This is a rollout-ranking heuristic, not an admissible distance
        estimate. A value of 1.0 means the cube is solved.
        """
        correctly_placed = 0
        correctly_oriented_stickers = 0
        fully_solved_corners = 0

        for corner_id, positions in enumerate(self.corner_positions):
            # Identify which original cubie occupies this destination corner.
            source_corners = {
                self.sticker_source_corner[state[position]]
                for position in positions
            }

            # In a valid cube state, all three stickers at a corner belong
            # to the same original corner cubie.
            if source_corners == {corner_id}:
                correctly_placed += 1

            exact_stickers = sum(
                state[position] == self.solved[position]
                for position in positions
            )
            correctly_oriented_stickers += exact_stickers

            if exact_stickers == 3:
                fully_solved_corners += 1

        return (
            0.40 * (correctly_placed / 8)
            + 0.30 * (correctly_oriented_stickers / 24)
            + 0.30 * (fully_solved_corners / 8)
        )

    def legal_actions(self, last_face=None):
        if last_face is None:
            # Return a fresh list: expand() removes actions from this list.
            # Returning self.actions aliases and destructively shrinks the
            # solver's global action set during search.
            return list(self.actions)
        return [
            a for a in self.actions
            if a[2] != last_face
        ]

    def select_child(self, node):
        log_n = math.log(max(1, node.visits))

        def uct(child):
            exploit = child.mean_reward
            explore = self.exploration * math.sqrt(
                log_n / child.visits
            )
            return exploit + explore

        return max(node.children, key=uct)

    def expand(self, node):
        action = self.rng.choice(node.untried_actions)
        node.untried_actions.remove(action)

        name, permutation, face = action
        state = self.apply_move(node.state, permutation)

        child = MCTSNode(
            state=state,
            parent=node,
            move=name,
            face=face,
            untried_actions=self.legal_actions(face),
        )
        node.children.append(child)

        self.stats["expanded_nodes"] += 1
        self.stats["max_tree_depth"] = max(
            self.stats["max_tree_depth"],
            self.node_depth(child),
        )
        return child

    @staticmethod
    def node_depth(node):
        depth = 0
        while node.parent is not None:
            depth += 1
            node = node.parent
        return depth

    def rollout(self, state, last_face=None):
        current = state
        previous_face = last_face
        moves = []
        best_h = self.heuristic(current)

        for _ in range(self.rollout_depth):
            if self.is_solved(current):
                return 1.0, moves, True, best_h

            actions = self.legal_actions(previous_face)
            action = self.rng.choice(actions)

            name, permutation, face = action
            current = self.apply_move(current, permutation)
            moves.append(name)
            previous_face = face

            self.stats["rollout_steps"] += 1
            best_h = max(best_h, self.heuristic(current))

        solved = self.is_solved(current)
        if solved:
            return 1.0, moves, True, best_h

        return 0.5 * self.heuristic(current), moves, False, best_h

    def backpropagate(self, node, reward):
        while node is not None:
            node.visits += 1
            node.reward += reward
            node = node.parent

    def reconstruct_path(self, node):
        path = []
        while node.parent is not None:
            path.append(node.move)
            node = node.parent
        return path[::-1]

    def verify_solution(self, start_state, moves):
        state = start_state
        action_map = {a[0]: a for a in self.actions}

        for name in moves:
            if name not in action_map:
                return False
            state = self.apply_move(state, action_map[name][1])

        return self.is_solved(state)

    def record_history(self, iteration, root, elapsed):
        self.history.append({
            "iteration": iteration,
            "elapsed_seconds": elapsed,
            "root_visits": root.visits,
            "root_mean_reward": root.mean_reward,
            "expanded_nodes": self.stats["expanded_nodes"],
            "rollout_steps": self.stats["rollout_steps"],
            "best_rollout_heuristic":
                self.stats["best_rollout_heuristic"],
        })

    def solve(self, start_state, iterations=50_000,
              time_limit=10.0):
        self.stats = {
            "iterations": 0,
            "expanded_nodes": 0,
            "rollout_steps": 0,
            "rollout_successes": 0,
            "max_tree_depth": 0,
            "best_rollout_heuristic": self.heuristic(start_state),
            "solution_found": False,
            "solution_length": None,
            "iterations_to_solution": None,
            "time_to_solution_seconds": None,
            "tree_search_seconds": 0.0,
            "rollout_seconds": 0.0,
            "elapsed_seconds": 0.0,
        }
        self.history = []

        overall_start = time.perf_counter()

        if self.is_solved(start_state):
            self.stats["solution_found"] = True
            self.stats["solution_length"] = 0
            self.stats["iterations_to_solution"] = 0
            self.stats["time_to_solution_seconds"] = 0.0
            self.stats["elapsed_seconds"] = 0.0
            return []

        root = MCTSNode(
            state=start_state,
            untried_actions=self.legal_actions(),
        )
        self.last_root = root
        solution = None

        for iteration in range(1, iterations + 1):
            if time.perf_counter() - overall_start >= time_limit:
                break

            node = root

            # 1. Selection
            tree_start = time.perf_counter()
            while not node.untried_actions and node.children:
                node = self.select_child(node)

            # 2. Expansion
            if self.is_solved(node.state):
                solution = self.reconstruct_path(node)
                self.backpropagate(node, 1.0)
                self.stats["iterations"] = iteration
                self.stats["iterations_to_solution"] = iteration
                self.stats["time_to_solution_seconds"] = (
                    time.perf_counter() - overall_start
                )
                self.stats["solution_found"] = True
                break

            if node.untried_actions:
                node = self.expand(node)

            self.stats["tree_search_seconds"] += (
                time.perf_counter() - tree_start
            )

            if self.is_solved(node.state):
                solution = self.reconstruct_path(node)
                self.backpropagate(node, 1.0)
                self.stats["iterations"] = iteration
                self.stats["iterations_to_solution"] = iteration
                self.stats["time_to_solution_seconds"] = (
                    time.perf_counter() - overall_start
                )
                self.stats["solution_found"] = True
                break

            # 3. Simulation
            rollout_start = time.perf_counter()
            reward, rollout_moves, solved, best_h = self.rollout(
                node.state, node.face
            )
            self.stats["rollout_seconds"] += (
                time.perf_counter() - rollout_start
            )
            self.stats["best_rollout_heuristic"] = max(
                self.stats["best_rollout_heuristic"], best_h
            )

            self.backpropagate(node, reward)
            self.stats["iterations"] = iteration

            if solved:
                candidate = (
                    self.reconstruct_path(node) + rollout_moves
                )
                if self.verify_solution(start_state, candidate):
                    solution = candidate
                    self.stats["rollout_successes"] += 1
                    self.stats["solution_found"] = True
                    self.stats["solution_length"] = len(solution)
                    self.stats["iterations_to_solution"] = iteration
                    self.stats["time_to_solution_seconds"] = (
                        time.perf_counter() - overall_start
                    )
                    break

            if (
                self.history_interval > 0
                and iteration % self.history_interval == 0
            ):
                self.record_history(
                    iteration, root,
                    time.perf_counter() - overall_start,
                )

        elapsed = time.perf_counter() - overall_start
        self.stats["elapsed_seconds"] = elapsed

        if solution is not None:
            if not self.verify_solution(start_state, solution):
                raise RuntimeError("Solution verification failed.")
            self.stats["solution_length"] = len(solution)

        if not self.history or (
            self.history[-1]["iteration"] != self.stats["iterations"]
        ):
            self.record_history(
                self.stats["iterations"], root, elapsed
            )

        return solution

    def report(self):
        print("\nMCTS run statistics")
        print("-" * 36)
        for key, value in self.stats.items():
            if isinstance(value, float):
                print(f"{key:32s}: {value:.6f}")
            else:
                print(f"{key:32s}: {value}")




def make_scramble(actions, depth, rng):
    """Generate a random scramble without consecutive same-face turns."""
    state_moves = []
    previous_face = None

    for _ in range(depth):
        choices = [
            a for a in actions
            if a[2] != previous_face
        ]
        action = rng.choice(choices)
        state_moves.append(action[0])
        previous_face = action[2]

    return state_moves


def apply_moves(state, moves, actions, apply_move):
    """Apply a sequence of named moves to a state."""
    action_map = {a[0]: a for a in actions}

    for name in moves:
        if name not in action_map:
            raise ValueError(f"Unknown move name: {name}")
        state = apply_move(state, action_map[name][1])

    return state


def run_unit_tests(solved, actions, apply_move):
    """Fast correctness tests independent of search performance."""
    print("\nRunning unit tests...")

    # Test 1: Solved state is recognized.
    solver = MCTSCubeSolver(solved, actions, apply_move, seed=1)
    assert solver.is_solved(solved)
    assert solver.solve(solved, iterations=10, time_limit=1) == []
    print("PASS: solved-state detection")

    # Test 2: Every move is a valid permutation of sticker positions.
    action_map = {a[0]: a for a in actions}
    for name, permutation, face in actions:
        assert len(permutation) == len(solved), name
        assert sorted(permutation) == list(range(len(solved))), name
        moved = apply_move(solved, permutation)
        assert len(moved) == len(solved), name
        assert sorted(moved) == sorted(solved), name
    print("PASS: move permutations preserve all stickers")

    # Test 3: A quarter-turn applied four times is the identity;
    # each clockwise turn followed by its inverse restores SOLVED.
    for face in "UDRLFB":
        quarter = action_map[face][1]
        state = solved
        for _ in range(4):
            state = apply_move(state, quarter)
        assert state == solved, f"{face}^4 should be identity"

        inverse = action_map[face + "'"][1]
        state = apply_move(apply_move(solved, quarter), inverse)
        assert state == solved, f"{face} followed by inverse failed"
    print("PASS: quarter-turn cycles and inverse moves")

    # Test 4: Applying a move and then its named inverse restores
    # any valid state, not just the solved state.
    scramble = make_scramble(actions, 5, random.Random(9))
    scrambled = apply_moves(solved, scramble, actions, apply_move)
    inverse_names = {"U":"U'", "U'":"U", "U2":"U2",
                     "D":"D'", "D'":"D", "D2":"D2",
                     "R":"R'", "R'":"R", "R2":"R2",
                     "L":"L'", "L'":"L", "L2":"L2",
                     "F":"F'", "F'":"F", "F2":"F2",
                     "B":"B'", "B'":"B", "B2":"B2"}
    restored = apply_moves(
        scrambled, [inverse_names[m] for m in reversed(scramble)],
        actions, apply_move
    )
    assert restored == solved
    print("PASS: scramble reversibility")

    # Test 5: Scrambles are reproducible for a fixed RNG seed.
    s1 = make_scramble(actions, 5, random.Random(123))
    s2 = make_scramble(actions, 5, random.Random(123))
    assert s1 == s2
    print("PASS: deterministic scramble generation")

    # Test 6: A generated scramble can be replayed consistently.
    scramble = make_scramble(actions, 3, random.Random(9))
    state = apply_moves(solved, scramble, actions, apply_move)
    replayed = apply_moves(solved, scramble, actions, apply_move)
    assert state == replayed
    print("PASS: scramble replay consistency")

    print("All unit tests passed.")


def benchmark_mcts(
    solved,
    actions,
    apply_move,
    depths=(1, 3, 5, 7, 9),
    trials=5,
    iterations=50_000,
    time_limit=5.0,
    rollout_depth=20,
    seed=1234,
):
    """
    Run repeated experiments and return one record per trial.

    Use the same saved scrambles and time budgets for comparisons
    with IDA*. Search outcomes are stochastic.
    """
    records = []
    master_rng = random.Random(seed)

    for depth in depths:
        for trial in range(trials):
            scramble_seed = master_rng.randrange(2**32)
            scramble_rng = random.Random(scramble_seed)

            scramble = make_scramble(
                actions, depth, scramble_rng
            )
            start_state = apply_moves(
                solved, scramble, actions, apply_move
            )

            solver_seed = master_rng.randrange(2**32)
            solver = MCTSCubeSolver(
                solved=solved,
                actions=actions,
                apply_move=apply_move,
                exploration=math.sqrt(2),
                rollout_depth=rollout_depth,
                seed=solver_seed,
                history_interval=100,
            )

            solution = solver.solve(
                start_state,
                iterations=iterations,
                time_limit=time_limit,
            )

            verified = (
                solution is not None
                and solver.verify_solution(start_state, solution)
            )

            stats = solver.stats
            record = {
                "scramble_depth": depth,
                "trial": trial + 1,
                "scramble_seed": scramble_seed,
                "solver_seed": solver_seed,
                "scramble": " ".join(scramble),
                "solved": int(verified),
                "solution_length": (
                    len(solution) if verified else None
                ),
                "iterations": stats["iterations"],
                "iterations_to_solution":
                    stats["iterations_to_solution"],
                "elapsed_seconds": stats["elapsed_seconds"],
                "time_to_solution_seconds":
                    stats["time_to_solution_seconds"],
                "expanded_nodes": stats["expanded_nodes"],
                "rollout_steps": stats["rollout_steps"],
                "rollout_successes": stats["rollout_successes"],
                "max_tree_depth": stats["max_tree_depth"],
                "best_rollout_heuristic":
                    stats["best_rollout_heuristic"],
                "tree_search_seconds":
                    stats["tree_search_seconds"],
                "rollout_seconds": stats["rollout_seconds"],
            }
            records.append(record)

            print(
                f"depth={depth:2d} trial={trial + 1:2d} "
                f"solved={verified!s:5s} "
                f"time={stats['elapsed_seconds']:.3f}s "
                f"nodes={stats['expanded_nodes']} "
                f"rollout_steps={stats['rollout_steps']}"
            )

    return records


def save_results_csv(records, filename="mcts_results.csv"):
    if not records:
        print("No results to save.")
        return

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)

    print(f"Saved {len(records)} trials to {filename}")


def summarize_results(records):
    """Print per-depth aggregate metrics."""
    depths = sorted(set(r["scramble_depth"] for r in records))

    print("\nAggregate benchmark results")
    print(
        f"{'Depth':>5} {'Success':>9} {'Mean time':>11} "
        f"{'Mean length':>12} {'Mean nodes':>12}"
    )

    for depth in depths:
        group = [
            r for r in records if r["scramble_depth"] == depth
        ]
        successes = [r for r in group if r["solved"]]
        rate = len(successes) / len(group)

        mean_time = statistics.mean(
            r["elapsed_seconds"] for r in group
        )
        mean_length = (
            statistics.mean(
                r["solution_length"] for r in successes
            ) if successes else float("nan")
        )
        mean_nodes = statistics.mean(
            r["expanded_nodes"] for r in group
        )

        print(
            f"{depth:5d} {rate:8.1%} {mean_time:10.3f}s "
            f"{mean_length:12.2f} {mean_nodes:12.1f}"
        )


def plot_results(records, filename="mcts_plots.png"):
    """Generate six benchmark plots."""
    if not records:
        return

    depths = sorted(set(r["scramble_depth"] for r in records))

    def grouped(metric, only_successes=False):
        result = []
        for depth in depths:
            group = [
                r for r in records
                if r["scramble_depth"] == depth
                and (not only_successes or r["solved"])
                and r[metric] is not None
            ]
            result.append(
                statistics.mean(r[metric] for r in group)
                if group else float("nan")
            )
        return result

    success_rate = [
        statistics.mean(
            r["solved"] for r in records
            if r["scramble_depth"] == depth
        )
        for depth in depths
    ]

    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    fig.suptitle("2x2x2 Rubik's Cube — MCTS Performance")

    plots = [
        (axes[0, 0], success_rate, "Success rate", "Fraction", False),
        (axes[0, 1], grouped("elapsed_seconds"),
         "Runtime", "Seconds", False),
        (axes[0, 2], grouped("solution_length", True),
         "Solution length (successful trials)", "Moves", False),
        (axes[1, 0], grouped("expanded_nodes"),
         "Expanded tree nodes", "Nodes", False),
        (axes[1, 1], grouped("rollout_steps"),
         "Rollout steps", "Steps", False),
        (axes[1, 2], grouped("iterations_to_solution", True),
         "Iterations to solution", "Iterations", False),
    ]

    for ax, values, title, ylabel, _ in plots:
        ax.plot(depths, values, marker="o")
        ax.set_title(title)
        ax.set_xlabel("Scramble length (moves)")
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3)

    axes[0, 0].set_ylim(0, 1.05)
    fig.tight_layout()
    fig.savefig(filename, dpi=160, bbox_inches="tight")
    plt.show()
    print(f"Saved plots to {filename}")


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


# Quarter-turn permutations
QUARTER_MOVES = {
    face: create_face_permutation(face)
    for face in FACES
}

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


def main():
    # SOLVED, ACTIONS, and apply_move must be defined above.
    run_unit_tests(SOLVED, ACTIONS, apply_move)

    results = benchmark_mcts(
        solved=SOLVED,
        actions=ACTIONS,
        apply_move=apply_move,
        depths=(1, 3, 5, 7, 9),
        trials=5,
        iterations=50_000,
        time_limit=5.0,
        rollout_depth=20,
        seed=1234,
    )

    save_results_csv(results)
    summarize_results(results)
    plot_results(results)


if __name__ == "__main__":
    main()
