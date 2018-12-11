import numpy as np

def shuffle(arr, n):
    for i in range(n-1, 0, -1):
        #pick a random index from 0 to i
        j = np.random.randint(low=0, high=i+1)
        #swap arr[i] with the element at random index
        arr[i], arr[j] = arr[j], arr[i]
    #end for
    return arr

arr = [1, 2, 3, 4, 5, 6, 7, 8]
n = len(arr)
print("Fisher-Yates shuffle:")
print(shuffle(arr, n))

