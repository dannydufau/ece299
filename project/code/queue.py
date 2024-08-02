class Queue:
    def __init__(self):
        self.queue = []

    def put(self, item):
        self.queue.append(item)

    def get(self):
        if not self.empty():
            return self.queue.pop(0)
        return None

    def empty(self):
        return len(self.queue) == 0

    def size(self):
        return len(self.queue)
