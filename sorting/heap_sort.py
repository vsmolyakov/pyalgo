def heapify(arr, n, i):
    largest = i #init largest as root
    l = 2 * i + 1  #left child
    r = 2 * i + 2  #right child

    if (l < n and arr[i] < arr[l]):
        largest = l

    if (r < n and arr[largest] < arr[r]):
        largest = r

    #update root if needed
    if largest != i:
        arr[i], arr[largest] = arr[largest], arr[i]
        #heapify the root
        heapify(arr, n, largest)

def heap_sort(arr):
    n = len(arr)

    #build a max heap
    for i in range(n, -1, -1):
        heapify(arr, n, i)

    #extract elements one by one
    for i in range(n-1, 0, -1):
        arr[i], arr[0] = arr[0], arr[i]
        heapify(arr, i, 0)


arr = [12, 11, 13, 5, 6, 7]
print("input array:")
print(arr)
print("heap sort:")
heap_sort(arr)
print(arr)

