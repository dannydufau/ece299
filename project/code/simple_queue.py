class SimpleQueue:
    def __init__(self):
        self.queue = []

    def put(self, item):
        self.queue.append(item)

    def get(self):
        if not self.is_empty():
            return self.queue.pop(0)
        return None

    def is_empty(self):
        return len(self.queue) == 0