def matching_parentheses(string):
    stack = []
    for char in string:
        if (char == '(' or char == '[' or char == '{'):
            stack.append(char) #push
        else:
            if (len(stack) == 0):
                return False
            if (char == ')' and stack[-1] != '('):
                return False
            if (char == ']' and stack[-1] != '['):
                return False
            if (char == '}' and stack[-1] != '{'):
                return False
            stack.pop()
        #end if
    #end for
    return len(stack) == 0

s1 = "{()}[]"
print("Q: Are parentheses balanced? : %s" %s1)
a1 = matching_parentheses(s1)
print "A: Yes" if a1 else "A: No"

s2 = "{([])))"
print("Q: Are parentheses balanced? : %s" %s2)
a2 = matching_parentheses(s2)
print "A: Yes" if a2 else "A: No"


