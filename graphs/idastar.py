from math import inf

def manhattan(a, b):
    """Manhattan distance between two grid positions."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def get_neighbors(grid, node):
    """Return valid neighboring cells."""
    rows = len(grid)
    cols = len(grid[0])

    r, c = node

    directions = [
        (-1, 0),  # up
        (1, 0),   # down
        (0, -1),  # left
        (0, 1),   # right
    ]

    neighbors = []

    for dr, dc in directions:
        nr = r + dr
        nc = c + dc

        if (
            0 <= nr < rows
            and 0 <= nc < cols
            and grid[nr][nc] != "#"
        ):
            neighbors.append((nr, nc))

    return neighbors


def ida_star(grid, start, goal):
    """
    IDA* search.

    Returns:
        path: list of positions from start to goal
        cost: path cost
    """

    # Initial threshold = h(start)
    # f(n) = g(n) + h(n)
    # g(n) is the cost from start to n
    # h(n) is the heuristic estimate from n to goal
    threshold = manhattan(start, goal)

    path = [start]
    visited = {start}   #set

    #nested function: a function defined inside another function
    #the main reason is that search() needs access to variables that
    #belong to the surrounding ida_star() function
    def search(node, g, threshold):
        """
        Depth-first search limited by f = g + h.

        Returns either:
            - a path when goal is found
            - the minimum f-cost that exceeded threshold
        """

        h = manhattan(node, goal)
        f = g + h

        # Node is outside current threshold
        if f > threshold:
            return f  #prune: do not explore node's neighbors and return new low threshold

        # Goal reached
        if node == goal:
            return list(path)

        minimum = inf   #used to keep track of smallest exceeded f-value

        for neighbor in get_neighbors(grid, node):

            # Avoid cycles in current path
            if neighbor in visited:
                continue

            visited.add(neighbor)
            path.append(neighbor)

            result = search(
                neighbor,
                g + 1,
                threshold
            )

            # Goal found
            if isinstance(result, list):
                return result

            # Keep track of smallest exceeded f-value
            minimum = min(minimum, result)

            # Backtrack: undo the move to neighbor
            # we finished exploring the neighbor
            # go back to previous position
            path.pop()
            visited.remove(neighbor)

        return minimum

    while True:

        result = search(
            start,
            g=0,
            threshold=threshold
        )

        # Solution found
        if isinstance(result, list):
            return result, len(result) - 1

        # No solution
        if result == inf:
            return None, inf

        # Increase threshold
        threshold = result

def print_grid(grid, path):
    grid_copy = [row[:] for row in grid]

    for r, c in path:
        if grid_copy[r][c] not in ("S","G"):
            grid_copy[r][c] = "*"

    for row in grid_copy:
        print(" ".join(row))


if __name__ == "__main__":

    grid = [
        ["S", ".", ".", "#", "."],
        [".", "#", ".", "#", "."],
        [".", "#", ".", ".", "."],
        [".", ".", "#", ".", "."],
        [".", ".", ".", ".", "G"],
    ]

    start = (0, 0)
    goal = (4, 4)

    path, cost = ida_star(grid, start, goal)

    print("Path:", path)
    print("Cost:", cost)
    print_grid(grid, path)
