
class Node:
    def __init__(self, k, v):
        #doubly linked list node
        self.key = k
        self.val = v
        self.prev = None
        self.next = None

class LRU:
    def __init__(self, capacity):
        self.capacity = capacity
        self.dic = dict() #hash table of doubly-linked lists
        self.head = Node(0, 0)
        self.tail = Node(0, 0)
        self.head.next = self.tail
        self.tail.prev = self.head

    def get(self, key):
        if key in self.dic:
            n = self.dic[key]
            self._remove(n) #remove node from doubly-linked list
            self._add(n) #add to the end of doubly-linked list
            return n.val
        return -1 #not found

    def put(self, key, value):
        if key in self.dic:
            self._remove(self.dic[key]) #remove previous value
        n = Node(key, value) #create a new Node
        self._add(n) #add at the end of doubly-linked list
        self.dic[key] = n
        if len(self.dic) > self.capacity:  #if reached capacity
            n = self.head.next   #get the next from head node (LRU)
            self._remove(n)      #remove it from doubly linked list
            del self.dic[n.key]  #delete its key

    def _remove(self, node):
        #remove node from doubly-linked list
        p = node.prev
        n = node.next
        p.next = n
        n.prev = p

    def _add(self, node):
        #add node at the end of doubly-linked list
        p = self.tail.prev
        p.next = node
        self.tail.prev = node
        node.prev = p
        node.next = self.tail


lru = LRU(3)
lru.put(1,1) #(key, value)
lru.put(2,2)
lru.put(3,3)
print(lru.get(1))   #returns 1 (value)
lru.put(4,4)        #removes key 2 (lru)
print(lru.get(1))   #returns 1 (value) 
print(lru.get(2))   #returns -1 (not found) 
print(lru.get(3))   #returns 3




