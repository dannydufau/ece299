import _thread
import time

class ThreadManager:
    def __init__(self):
        self.thread_running = False

    def start_thread(self, target):
        if not self.thread_running:
            self.thread_running = True
            _thread.start_new_thread(target, ())

    def stop_thread(self):
        self.thread_running = False
        time.sleep(0.2)  # Allow time for the thread to exit

