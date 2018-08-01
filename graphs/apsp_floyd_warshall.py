
V = 4 #number of vertices
INF = 99999 #infinity

def apsp_floyd_warshall(graph):
    dist = map(lambda i: map(lambda j: j, i), graph) 

    for k in range(V):
        for i in range(V):
            for j in range(V):
                dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])

    print_solution(dist)


def print_solution(dist):
    print("all pairs shortest paths")
    for i in range(V):
        for j in range(V):
            if (dist[i][j] == INF):
                print "%7s" %("INF"), 
            else:
                print "%7d\t" %(dist[i][j]), 
        print ""

#weighted graph
"""
       10
  (0) ----> (3)
   |        /|\
 5 |         | 1
  \|/        |
  (1) ----> (2)
        3
"""

graph = [[  0,   5, INF,  10],
         [INF,   0,   3, INF],
         [INF, INF,   0,   1],
         [INF, INF, INF,   0]]

apsp_floyd_warshall(graph)
