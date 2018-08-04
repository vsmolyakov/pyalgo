class Node:
    def __init__(self, key):
        self.left = None
        self.right = None
        self.val = key

def insert(root, node):
    if root == None:
        root = node
    else:
        if root.val < node.val:
            if root.right is None:
                root.right = node
            else:
                insert(root.right, node)
        else:
            if root.left is None:
                root.left = node
            else:
                insert(root.left, node)
        #end if
    #end if

def inorder(root):
    if root == None:
        return

    inorder(root.left)
    print root.val, 
    inorder(root.right)

"""
         50
       /    \
      30    70
     /  \  /  \
    20 40 60  80 
"""

r = Node(50)
insert(r, Node(30))
insert(r, Node(20))
insert(r, Node(40))
insert(r, Node(70))
insert(r, Node(60))
insert(r, Node(80))

print("inorder traversal:")
inorder(r)
