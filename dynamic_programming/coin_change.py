
def count(S, m, n):
    #bottom-up DP
    #S: coin value array, m: number of coins, n: sum
    table = [[0 for x in range(m)] for y in range(n+1)]
    
    #when n = 0 return 1
    for i in range(m):
        table[0][i] = 1

    #consider including m-th coin and excluding it
    for i in range(1, n+1):
        for j in range(m):
            #count of solutions inclucing coin S[j]
            x = table[i - S[j]][j] if i - S[j] >= 0 else 0

            #count of solutions excluding coin S[j]
            y = table[i][j-1] if j >= 1 else 0

            table[i][j] = x + y
        #end for
    #end for
    print("DP table:")
    print(table)
    return table[n][m-1]


arr = [1, 2, 3]
m = len(arr)
n = 4
print("given {} coins with values: {}".format(m, arr))
num_ways = count(arr, m, n)
print("the number of ways to compute change that sums to %d :" %(n))
print(num_ways)

