M = 8
N = 8
component_count = 0

def flood_fill_util(screen, x, y, prevC, newC):
    #base case
    if (x < 0 or x >= M or y < 0 or y >= N):
        return
    if (screen[x][y] != prevC):
        return

    #replace the color at (x, y)
    global component_count
    screen[x][y] = newC
    component_count += 1

    flood_fill_util(screen, x-1, y, prevC, newC)
    flood_fill_util(screen, x+1, y, prevC, newC)
    flood_fill_util(screen, x, y-1, prevC, newC)
    flood_fill_util(screen, x, y+1, prevC, newC)

def flood_fill(screen, x, y, newC):
    prevC = screen[x][y]
    flood_fill_util(screen, x, y, prevC, newC)
    return screen

def print_matrix(arr):
    for i in range(len(arr)):
        print(" ".join(map(str, arr[i])))
    print ""
        
screen = [[1, 1, 1, 1, 1, 1, 1, 1],
          [1, 1, 1, 1, 1, 1, 0, 0],
          [1, 0, 0, 1, 1, 0, 1, 1],
          [1, 2, 2, 2, 2, 0, 1, 0],
          [1, 1, 1, 2, 2, 0, 1, 0],
          [1, 1, 1, 2, 2, 2, 2, 0],
          [1, 1, 1, 1, 1, 2, 1, 1],
          [1, 1, 1, 1, 1, 2, 2, 1]]

print("input array:")
print_matrix(screen)

x = 4
y = 4
newC=3
print("flood fill (x,y) = ({},{}) with new color = {}:".format(x, y, newC))
flood_fill(screen, x, y, newC)
print_matrix(screen)
print("number of pixels: %d" %(component_count))
