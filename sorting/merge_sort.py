def merge(arr, l, m, r):
    n1 = m - l + 1
    n2 = r - m

    #create temp arrays
    L = [0] * (n1)
    R = [0] * (n2)

    for i in range(0, n1):
        L[i] = arr[l + i]

    for j in range(0, n2):
        R[j] = arr[m + 1 + j]

    #merge the temp arrays back into arr[l..r]
    i = 0 #init index of first sub-array
    j = 0 #init index of second sub-array
    k = l #init index of merged sub-array

    while i < n1 and j < n2:
        if L[i] <= R[j]:
            arr[k] = L[i]
            i += 1
        else:
            arr[k] = R[j]
            j += 1
        k += 1

    #copy remaining elements of L if any
    while i < n1:
        arr[k] = L[i]
        i += 1
        k += 1

    #copy remaining elements of R if any
    while j < n2:
        arr[k] = R[j]
        j += 1
        k += 1


def merge_sort(arr, l, r):
    if l < r:
        m = l + (r-l)/2

        merge_sort(arr, l, m)
        merge_sort(arr, m+1, r)
        merge(arr, l, m, r)


arr = [12, 11, 13, 5, 6, 7]
n = len(arr)
print("input array:")
print(arr)
print("merge sort:")
merge_sort(arr, 0, n-1)
print(arr)

