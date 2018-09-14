
def partition(arr, l, r):
    x = arr[r]
    i = l
    for j in range(l, r):
        if (arr[j] <= x):
            arr[i], arr[j] = arr[j], arr[i]
            i += 1
        #end if
    #end for
    arr[i], arr[r] = arr[r], arr[i]
    return i

def kth_smallest(arr, l, r, k):
    
    if (k < 0 or k > r-l+1):
        return -1;

    #parition the array (similar to quicksort)
    index = partition(arr, l, r)

    #if position same as k return rank-k element
    if (index - l == k - 1):
        return arr[index]

    #if rank-k element is less, look in the left sub-array
    if (index - l > k - 1):
        return kth_smallest(arr, l, index - 1, k)
    else: #look in right sub-array
        return kth_smallest(arr, index+1, r, k - index + l - 1)
    #end if

arr = [10, 4, 5, 8, 6, 11, 26] #assumes distinct elements
n = len(arr)
k = 3 #rank

print("input array:")
print(arr)
result = kth_smallest(arr, 0, n-1, k)
print("kthe smallest element (k={}) is {}".format(k, result))
