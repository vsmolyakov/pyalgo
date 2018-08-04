def remove_element(nums, val):
    #k: slow moving pointer, i: fast moving pointer
    k = 0
    for i in range(len(nums)):
        if (nums[i] != val):
            nums[k] = nums[i]
            k += 1
        #end if
    #end for

    return k  #new container size

item = 5
nums = [1, 2, 3, 4, 5, 6, 7]
print("input array:")
print(nums)
print("element to remove in place: {}".format(item))
k = remove_element(nums, item)
print("output array:")
print(nums[:k])
