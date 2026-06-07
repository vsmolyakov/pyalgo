class CelebrityProblem:
    def __init__(self, matrix):
        self.matrix = matrix
        self.n = len(matrix)

    def knows(self, a, b):
        return self.matrix[a][b] == 1

    def find_celebrity_recursive(self, left, right):
        # Base case
        if left == right:
            return left

        mid = (left + right) // 2

        # Find celebrity candidates in both halves
        c1 = self.find_celebrity_recursive(left, mid)
        c2 = self.find_celebrity_recursive(mid + 1, right)

        # Combine step
        if self.knows(c1, c2):
            return c2
        else:
            return c1

    def find_celebrity(self):
        if self.n == 0:
            return -1

        candidate = self.find_celebrity_recursive(0, self.n - 1)

        # Verify candidate
        for i in range(self.n):
            if i == candidate:
                continue

            # Celebrity knows nobody
            if self.knows(candidate, i):
                return -1

            # Everyone knows celebrity
            if not self.knows(i, candidate):
                return -1

        return candidate


# Example
matrix = [
    [0, 1, 1, 1],
    [0, 0, 1, 1],
    [0, 0, 0, 0],  # Person 2 is celebrity
    [0, 1, 1, 0]
]

cp = CelebrityProblem(matrix)

celebrity = cp.find_celebrity()

if celebrity != -1:
    print(f"Celebrity is person {celebrity}")
else:
    print("No celebrity found")