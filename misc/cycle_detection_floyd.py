def next(n):
    sum = 0
    #compute sum of squared digits
    #e.g. 19 -> 1^2 + 9^2 = 82
    while (n != 0):
        sum += pow(n % 10, 2)
        n = n / 10

    return sum

def isHappy(n):
    #a number n is happy if sum of
    #squared digits converges to 1

    slow = next(n)
    fast = next(next(n))

    print("slow: {}, fast: {}".format(slow, fast))

    while (slow != fast):
        slow = next(slow)
        fast = next(next(fast))
        print("slow: {}, fast: {}".format(slow, fast))

    return fast == 1


n = 19
print("Is number {} happy?".format(n))
print("(i.e. does the sum of digits squared converge to 1)")

result = isHappy(n)
print "Yes" if result else "No"


