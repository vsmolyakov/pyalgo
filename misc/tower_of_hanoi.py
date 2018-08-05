
def tower_of_hanoi(n, from_rod, to_rod, aux_rod):
    if n == 1:
        print("Move disk 1 from rod {} to rod {}".format(from_rod, to_rod))
        return

    tower_of_hanoi(n-1, from_rod, aux_rod, to_rod)
    print("Move disk {} from rod {} to rod {}".format(n, from_rod, to_rod))
    tower_of_hanoi(n-1, aux_rod, to_rod, from_rod)


n = 4
tower_of_hanoi(n, 'A', 'C', 'B')

