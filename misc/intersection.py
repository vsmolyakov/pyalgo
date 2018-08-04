def intersect(nums1, nums2):
    result = []
    hist = {} 

    for item in nums1:
        if item in hist:
            hist[item] += 1
        else:
            hist[item] = 1

    for item in nums2:
        if item in hist:
            hist[item] -= 1
            if (hist[item] >= 0):
                result.append(item)
        #end if
    #end for
    return result

nums1 = [1, 2, 3, 4, 5, 6, 7]
nums2 = [4, 5, 6, 7, 8, 9, 10]

print("nums1:")
print(nums1)
print("nums2:")
print(nums2)
print("intersection:")
intersection = intersect(nums1, nums2)
print(intersection)

