class InfiniteCounter:
    def __init__(self, start=0):
        self.current = start

    def __iter__(self):
        return self

    def __next__(self):
        current_value = self.current
        self.current += 1
        return current_value

# Usage:
counter = InfiniteCounter(10)
for num in counter:
    if num > 20:
        break
    print(num)
