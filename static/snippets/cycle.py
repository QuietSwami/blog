class Cycle:
    def __init__(self, data):
        self.data = data
        self.index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if not self.data:
            raise StopIteration
        result = self.data[self.index % len(self.data)]
        self.index += 1
        return result

# Usage:
cycler = Cycle([1, 2, 3])
for _ in range(10):
    print(next(cycler), end=' ')  # Prints: 1 2 3 1 2 3 1 2 3 1
