
class Graph:
    def __init__(self, V):
        self.V = V
        self.graph = [[0 for col in range(V)] for row in range(V)]

    def is_bipartite(self, src):
        
        colorArr = [-1] * self.V  #init color array
        colorArr[src] = 1 #set first color

        #BFS traversal with alternating colors
        #if neighbors have the same color return not bipartite
        queue = []
        queue.append(src)

        while queue:
            u = queue.pop()

            if self.graph[u][u]: 
                return False #self-loop

            #find neighbors in adj matrix
            for v in range(self.V):
                if (self.graph[u][v] and colorArr[v] == -1):
                    colorArr[v] = 1 - colorArr[u]
                    queue.append(v)

                elif self.graph[u][v] and colorArr[u] == colorArr[v]:
                    return False
            #end for
        #end while

        return True

g = Graph(4);
g.graph = [[0, 1, 0, 1],
           [1, 0, 1, 0],
           [0, 1, 0, 1],
           [1, 0, 1, 0]]

print("Is graph G bi-partite?")
print "Yes" if g.is_bipartite(0) else "No"
                




