
def count_sort(arr, exp1):
    
    n = len(arr)
    output = [0] * (n)
    count = [0] * (10)

    #build the digit histogram
    for i in range(0, n):
        index = (arr[i] / exp1)
        count[(index) % 10] += 1

    #make it cumulative
    for i in range(1, 10):
        count[i] += count[i-1]

    #index output array by cumulative histogram
    #and decrement corresponding value
    i = n-1
    while i >= 0:
        index = (arr[i] / exp1)
        output[count[(index) %10 ]-1] = arr[i]
        count[(index) % 10 ] -= 1
        i -= 1

    #write out the result
    i = 0
    for i in range(0, len(arr)):
        arr[i] = output[i]

def radix_sort(arr):
    
    #find the max number to figure out the number of digits
    max1 = max(arr)

    #do count sort for every digit, instead of passing the 
    #digit number, exp is passed, exp is 10^i where i is the
    #current digit number
    exp = 1
    while max1 / exp > 0:
        count_sort(arr, exp)
        exp = exp * 10


arr = [170, 45, 75, 90, 802, 24, 2, 66]
print("input array:")
print(arr)
print("radix sort:")
radix_sort(arr)
print(arr)



