from simple_queue import SimpleQueue


class QueueHandler:
    def __init__(self):
        self.queue = SimpleQueue()

    def add_to_queue(self, item):
        self.queue.put(item)

    def dequeue(self):
        if not self.queue.is_empty():
            return self.queue.get()
        return None

    def is_empty(self):
        return self.queue.is_empty()
