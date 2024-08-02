import _thread
import utime


class ThreadManager:
    def __init__(self):
        self.threads = []
        self.lock = _thread.allocate_lock()
        self.stop_flag = False

    def start_thread(self, target, *args):
        thread_id = len(self.threads)
        self.lock.acquire()
        try:
            self.threads.append(
                (
                    thread_id,
                    _thread.start_new_thread(
                        self.thread_wrapper, (target, thread_id) + args
                    ),
                )
            )
        finally:
            self.lock.release()
        return thread_id

    def thread_wrapper(self, target, thread_id, *args):
        try:
            target(*args)
        finally:
            self.lock.acquire()
            try:
                self.threads = [t for t in self.threads if t[0] != thread_id]
            finally:
                self.lock.release()

    def stop_thread(self):
        self.stop_flag = True

    def is_stopped(self):
        return self.stop_flag

    def wait_for_stop(self):
        while self.threads:
            utime.sleep(0.1)
