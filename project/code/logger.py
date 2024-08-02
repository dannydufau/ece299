import utime
import uos
import traceback
import inspect
import sys


class Logger:
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40

    def __init__(
        self,
        stdout_file="stdout.txt",
        stderr_file="stderr.txt",
        level=DEBUG,
        max_size=1024,
    ):
        self.stdout_file = stdout_file
        self.stderr_file = stderr_file
        self.level = level
        self.max_size = max_size  # Max size in bytes

    def _get_timestamp(self):
        current_time = utime.localtime()
        return "{:04}-{:02}-{:02} {:02}:{:02}:{:02}".format(
            current_time[0],
            current_time[1],
            current_time[2],
            current_time[3],
            current_time[4],
            current_time[5],
        )

    def _write(self, message, file_path):
        try:
            if uos.stat(file_path)[6] > self.max_size:
                self._rotate_file(file_path)

        except OSError:
            # File does not exist yet, so no need to rotate
            pass

        with open(file_path, "a") as f:
            f.write(message + "\n")

    def _rotate_file(self, file_path):
        with open(file_path, "r") as f:
            lines = f.readlines()

        with open(file_path, "w") as f:
            f.write("".join(lines[1:]))

    def debug(self, message):
        if self.level <= Logger.DEBUG:
            log_message = f"{self._get_timestamp()} DEBUG: {message}"
            # self._write(log_message, self.stdout_file)

            # Also print to console
            print(log_message)

    def info(self, message):
        if self.level <= Logger.INFO:
            log_message = f"{self._get_timestamp()} INFO: {message}"
            # self._write(log_message, self.stdout_file)
            print(log_message)

    def warning(self, message):
        if self.level <= Logger.WARNING:
            log_message = f"{self._get_timestamp()} WARNING: {message}"
            # self._write(log_message, self.stdout_file)
            print(log_message)

    def error(self, e, message=""):
        log_message = f"[ERROR] {self._get_timestamp()} - {message}\n"
        # self._write(log_message, self.stderr_file)
        print(log_message)
        sys.print_exception(e)

        # with open(self.stderr_file, "a") as f:
        #    sys.print_exception(e, f)

    def set_level(self, level):
        self.level = level


if __name__ == "__main__":
    # Test sync
    logger = Logger(level=Logger.INFO, max_size=2048)

    logger.debug("This is a debug message.")
    logger.info("This is an info message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")

    logger.set_level(Logger.DEBUG)
    logger.debug("This debug message will now be logged.")

    # Test error
    logger = Logger(level=Logger.INFO, max_size=2048)

    logger.debug("This is a debug message.")
    logger.info("This is an info message.")
    key = []
    try:
        # raise ValueError("This is an error message.")
        key[1]
    except Exception as e:
        logger.error(e, "oops")

    logger.set_level(Logger.DEBUG)
    logger.debug("This debug message will now be logged.")
