def max_sum(arr, n, k):
    if (n < k):
        print("Error: n < k")
        return -1

    max_sum = 0
    for i in range(k):
        max_sum += arr[i]

    window_sum = max_sum
    for i in range(k, n):
        window_sum += arr[i] - arr[i-k]
        max_sum = max(window_sum, max_sum)

    return max_sum

print("input array:")
arr = [1, 4, 2, 10, 2, 3, 1, 0, 20]
print(arr)
k = 4
n = len(arr)
ms = max_sum(arr, n, k)
print("max sum in a window of size %d: " %k)
print(ms)
