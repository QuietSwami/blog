class TreeNode:
    def __init__(self, key):
        self.left = None
        self.right = None
        self.val = key

class BinaryTree:
    def __init__(self, root):
        self.root = root

    def __iter__(self):
        return self.in_order_traversal(self.root)

    def in_order_traversal(self, node):
        if node:
            yield from self.in_order_traversal(node.left)
            yield node.val
            yield from self.in_order_traversal(node.right)

# Usage:
root = TreeNode(1)
root.left = TreeNode(2)
root.right = TreeNode(3)
root.left.left = TreeNode(4)
root.left.right = TreeNode(5)

tree = BinaryTree(root)
for value in tree:
    print(value)
