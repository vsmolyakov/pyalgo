import collections
import numpy as np


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
    ( 1,  1,  1),   # 0 URF
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


    def search(
        self,
        state,
        depth,
        bound,
        last_face
    ):
        """
        Depth-first search for one IDA* iteration.
        """

        self.nodes += 1

        h = heuristic(state)

        f = depth + h

        # f = g + h
        if f > bound:
            return f

        # Goal
        if state == SOLVED:
            return True

        minimum = float("inf")


        for name, permutation, face in ACTIONS:

            # Prune redundant moves.
            if should_prune(
                last_face,
                face
            ):
                continue


            next_state = apply_move(
                state,
                permutation
            )

            self.path.append(name)

            result = self.search(
                next_state,
                depth + 1,
                bound,
                face
            )

            if result is True:
                return True

            self.path.pop()


            # IDA* needs the smallest f-value that exceeded
            # the current bound.
            if result < minimum:
                minimum = result


        return minimum


    def solve(
        self,
        state,
        max_depth=11
    ):
        """
        Solve the cube using IDA*.
        """

        self.nodes = 0
        self.path = []

        bound = heuristic(state)

        print(
            f"Initial heuristic = {bound}"
        )


        while bound <= max_depth:

            print(
                f"IDA* depth bound = {bound}"
            )

            result = self.search(
                state,
                0,
                bound,
                None
            )

            if result is True:

                return self.path.copy()

            bound = result


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
# 14. EXAMPLE
# ============================================================

if __name__ == "__main__":

    scramble = (
        "R U R2 F D F2 U"
    )

    print()
    print("Scramble:")
    print(scramble)

    cube = scramble_cube(scramble)

    solver = IDAStarSolver()

    solution = solver.solve(
        cube,
        max_depth=11
    )

    print()
    print("Solution:")
    print(" ".join(solution))

    print()
    print("Number of moves:")
    print(len(solution))

    print()
    print("Nodes searched:")
    print(solver.nodes)

    # Verify
    final_state = apply_solution(
        cube,
        solution
    )

    print()
    print("Solved:")
    print(final_state == SOLVED)