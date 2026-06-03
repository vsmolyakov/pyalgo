
class EightQueens:
    def __init__(self, n=8):
        self.n = n
        self.solutions = []
    
    def is_safe(self, queens, row, col):
        """
        check whether a queen can be places at (row, col)
        a state is represented by queens[row] = col
        e.g. queens = [0, 4, 7, 5, 2, 6, 1, 3] means that there are 8 queens
        placed at (0, 0), (1, 4), (2, 7), (3, 5), (4, 2), (5, 6), (6, 1), (7, 3)
        """

        for r in range(row):
            c = queens[r]
            if c == col or abs(c - col) == abs(r - row):
                return False

        return True
    
    def search(self, queens, row):
        """
        search for all possible placements of queens with backtracking
        """

        #goal state: all queens are placed
        if row == self.n:
            self.solutions.append(queens[:].copy())
            return
        
        #try every column in the current row
        for col in range(self.n):
            if self.is_safe(queens, row, col):
                queens[row] = col
                self.search(queens, row + 1) #recurse
                queens[row] = -1 #backtrack
    
    def solve(self):
        queens = [-1] * self.n 
        self.search(queens, 0) 
        return self.solutions

    def print_board(self, queens):
        for row in range(self.n):
            line = ""
            for col in range(self.n):
                if queens[row] == col:
                    line += "Q "
                else:
                    line += ". "
            print(line)
        print("\n")
    
if __name__ == "__main__":

    n_queens = EightQueens()
    solutions = n_queens.solve()
    print(f"Total solutions: {len(solutions)}")
    print("First solution:")
    n_queens.print_board(solutions[0]) 