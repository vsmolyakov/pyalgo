def partition(arr, low, high):
    #take the last element as pivot
    i = low - 1
    pivot = arr[high]

    #place pivot at its correct position and place all elements
    #smaller than the pivot to the left and all greater to the right
    for j in range(low, high):
        if (arr[j] <= pivot):
            i = i+1 #increment index of smaller element
            arr[i], arr[j] = arr[j], arr[i]
    
    arr[i+1], arr[high] = arr[high], arr[i+1]
    return i + 1

def quick_sort(arr, low, high):
    if low < high:
        #pi is now at the correct place
        pi = partition(arr, low, high)
        #sort before and after partition
        quick_sort(arr, low, pi-1)
        quick_sort(arr, pi+1, high)

arr = [10, 7, 8, 9, 1, 5]
n = len(arr)
print("input array:")
print(arr)
print("quick sort:")
quick_sort(arr, 0, n-1)
print(arr)
