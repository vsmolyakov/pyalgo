import heapq
from itertools import count

def manhattan_distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def find_position(grid, value):
    for y, row in enumerate(grid):
        for x, cell in enumerate(row):
            if cell == value:
                return (x, y)
    return None

def reconstruct_path(came_from, current):
    path = [current]

    while current in came_from:
        current = came_from[current]
        path.append(current)

    path.reverse()
    return path

def astar(grid):
    """
    A* search for a 2D grid.

    Returns:
        path: List of (row, col) coordinates, or None
        cost: Total path cost, or None
    """

    rows = len(grid)
    cols = len(grid[0])

    start = find_position(grid, 'S')
    goal = find_position(grid, 'G')

    directions = [
        (0, 1),   # right
        (0, -1),  # left
        (1, 0),   # down
        (-1, 0)   # up
    ]

    # Priority queue: (f_score, counter, position)
    # f(n) = g(n) + h(n)
    # g(n) is the cost from start to n
    # h(n) is the heuristic estimate from n to goal
    open_set = []
    counter = count()

    #init min-heap: heapq.heappush(heap, item)
    heapq.heappush(open_set, (manhattan_distance(start, goal), next(counter), start))

    # Actual cost from start
    # dictionary = {(r,c): cost from start to (r,c)}
    g_score = {start: 0}

    # Parent pointers
    # dictionary = {(r,c): parent of (r,c) in the path from start}
    came_from = {}

    while open_set:

        # Pop the node with the lowest f_score from the open set
        # (f_score, counter, position)
        f_current, _, current = heapq.heappop(open_set)

        # Skip outdated queue entries
        if f_current > g_score[current] + manhattan_distance(current, goal):
            continue

        # Goal reached
        if current == goal:
            path = reconstruct_path(came_from, current)
            return path, g_score[goal]

        r, c = current

        # Explore neighboring cells
        for dr, dc in directions:

            nr = r + dr
            nc = c + dc

            neighbor = (nr, nc)

            # Check grid boundaries
            if not (0 <= nr < rows and 0 <= nc < cols):
                continue

            # Check obstacles
            if grid[nr][nc] == '#':
                continue

            # Calculate tentative cost
            # tentative because we haven't established whether
            # this is the cheapest way to reach that neighbor.
            tentative_g = g_score[current] + 1

            # Update if a better path is found
            # tentative_g is the new path cost
            # g_score[neighbor] is the current best known cost to reach the neighbor
            if tentative_g < g_score.get(neighbor, float('inf')):

                # better (lower cost) path is found
                came_from[neighbor] = current     #update parent pointer
                g_score[neighbor] = tentative_g   #update actual cost from start

                f_neighbor = tentative_g + manhattan_distance(neighbor, goal)

                #item = (f_score, counter, position)
                heapq.heappush(open_set,(f_neighbor, next(counter), neighbor))

    # No path found
    return None, None


def print_grid(grid, path):
    """Print grid with the discovered path."""
    result = [row.copy() for row in grid]

    if path:
        for r, c in path:
            if result[r][c] not in ('S', 'G'):
                result[r][c] = '*'

    for row in result:
        print(' '.join(row))

if __name__ == "__main__":
   
    grid = [ 
        ['S', '.', '.', '#', '.'],
        ['.', '#', '.', '#', '.'],
        ['.', '#', '.', '.', '.'],
        ['.', '.', '#', '#', '.'],
        ['#', '.', '.', '.', 'G']
    ]

    path, cost = astar(grid)

    if path:
        print("Path:", path)
        print("Cost:", cost)
        print("\nGrid with path:")
        print_grid(grid, path)
    else:
        print("No path found")


