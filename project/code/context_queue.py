from queue import Queue


class Context:
    def __init__(self, router_context=None, ui_context=None):
        self.router_context = router_context or {}
        self.ui_context = ui_context or {}


class ContextQueue:
    def __init__(self):
        self.queue = Queue()
        self.size_counter = 0

    def add_to_queue(self, context):
        self.queue.put(context)
        self.size_counter += 1

    def dequeue(self):
        if not self.queue.empty():
            self.size_counter -= 1
            return self.queue.get()
        return None

    def is_empty(self):
        return self.queue.empty()

    def size(self):
        return self.size_counter


# Initialize global context queue instances
context_queue = ContextQueue()
auxiliary_queue = ContextQueue()
reporting_queue = ContextQueue()

# Basic usage example for testing
if __name__ == "__main__":
    # Create some context objects
    context1 = Context(router_context={"next_ui_id": "main_menu"}, ui_context={"header": "Main Menu"})
    context2 = Context(router_context={"next_ui_id": "settings_menu"}, ui_context={"header": "Settings Menu"})

    # Enqueue the context objects
    context_queue.add_to_queue(context1)
    print(f"Enqueued context1. Queue size: {context_queue.size()}")
    context_queue.add_to_queue(context2)
    print(f"Enqueued context2. Queue size: {context_queue.size()}")

    # Dequeue the context objects
    dequeued_context1 = context_queue.dequeue()
    print(f"Dequeued context1. Queue size: {context_queue.size()}")
    dequeued_context2 = context_queue.dequeue()
    print(f"Dequeued context2. Queue size: {context_queue.size()}")

    # Check if queue is empty
    print(f"Is queue empty? {context_queue.is_empty()}")
