class FileIterator:
    def __init__(self, filepath):
        self.filepath = filepath

    def __iter__(self):
        self.file = open(self.filepath, 'r')
        return self

    def __next__(self):
        line = self.file.readline()
        if line == '':
            self.file.close()
            raise StopIteration
        return line.strip()

# Usage:
file_iter = FileIterator('example.txt')
for line in file_iter:
    print(line)
