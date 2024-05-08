def outer(x):
    def inner(y):
        return x + y
    return inner

adding = outer(9) # At this moment, the outer function is initialized with the argument 5.
result = adding(10) # now we initilize the inner function with argument 6
print(result) # Result: 19