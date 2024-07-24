import machine
import utime
import uos
import random
from ds1307 import DS1307
from square_wave_generator import SquareWaveGenerator


class RealTimeClock:
    CONFIG_FILE = "time_mode_config.txt"
    SNOOZE_FILE_PREFIX = "snooze_"
    ALARM_FILE_PREFIX = "alarm_"
    ALARM_FILE_SUFFIX = ".txt"

    def __init__(self):
        self.weekday_map = {
            "sunday": 0,
            "monday": 1,
            "tuesday": 2,
            "wednesday": 3,
            "thursday": 4,
            "friday": 5,
            "saturday": 6
        }

        self.reverse_weekday_map = {v: k for k, v in self.weekday_map.items()}

        # Initialize I2C0
        i2c = machine.I2C(0, sda=machine.Pin(16), scl=machine.Pin(17))

        # Initialize DS1307
        self.rtc = DS1307(i2c)
        self.is_12_hour = self.load_time_mode() == 0  # Load time mode configuration

        # Set the time (year, month, day, weekday, hour, minute, second)
        current_time = self.rtc.datetime()
        print(f"Loaded RTC. Time: {current_time}")

        # Initialize alarm active flag
        self.alarm_active = False
    
        # Create alarm sound instances
        self.alarm = SquareWaveGenerator(22, 888)  # GP22, 1 kHz frequency

    def is_alarm_active(self):
        """
        Check if any alarm is currently active.
        """
        return self.alarm_active
    
    def alarm_on(self):
        self.alarm_active = True
        self.alarm.start()
    
    def alarm_off(self):
        self.alarm_active = False
        self.alarm.stop()

    def set_datetime(self, year, month, day, weekday, hour, minute, second):
        # Normalize the weekday to an integer
        if isinstance(weekday, str):
            weekday_lower = weekday.lower()
            # Default to 0 (Sunday) if not found
            weekday_int = self.weekday_map.get(weekday_lower, 0)
        else:
            weekday_int = weekday

        try:
            print(f"Setting RTC datetime to: {year}-{month}-{day} {hour}:{minute}:{second} Weekday: {weekday_int}")
            self.rtc.datetime((year, month, day, weekday_int, hour, minute, second))
        except Exception as e:
            print(f"Failed setting the date and time.\n{e}")

    def convert_to_12_hour(self, hour):
        if hour == 0:
            return 12, 'AM'
        elif hour == 12:
            return 12, 'PM'
        elif hour > 12:
            return hour - 12, 'PM'
        else:
            return hour, 'AM'

    def load_time_mode(self):
        try:
            if self.file_exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, 'r') as file:
                    mode = int(file.read().strip())
                    print(f"Time mode {mode} loaded from {self.CONFIG_FILE}")
                    return mode
        except Exception as e:
            print(f"Failed to load time mode. Defaulting to 24-hour mode. Error: {e}")
        # Default to 24-hour mode if loading fails
        return 1

    def find_alarm_by_time(self, alarm):
        """
        Find the alarm ID by time. Return None if no match is found.
        """
        for alarm_id, alarm_time in self.get_all_alarm_times():  # Use get_all_alarm_times to include snoozes
            print(f"FIND: alarm_time: {alarm_time}, alarm: {alarm}")
            if (alarm_time['hour'] == alarm['hour'] and
                alarm_time['minute'] == alarm['minute'] and
                alarm_time['second'] == alarm['second']):
                return alarm_id
        return None

    def find_alarm_by_timeBaK(self, alarm):
        """
        Find the alarm ID by time. Return None if no match is found.
        """
        for alarm_id, alarm_time in self.get_alarm_times():
            print(f"FIND: alarm_time: {alarm_time}, alarm: {alarm}")
            if (alarm_time['hour'] == alarm['hour'] and
                alarm_time['minute'] == alarm['minute'] and
                alarm_time['second'] == alarm['second']):
                return alarm_id
        return None
    
    def delete_alarm(self, alarm_id):
        """
        Delete the alarm file corresponding to the given alarm ID.
        """
        alarm_file = f"{self.ALARM_FILE_PREFIX}{alarm_id}{self.ALARM_FILE_SUFFIX}"
        try:
            if self.file_exists(alarm_file):
                uos.remove(alarm_file)
                print(f"Deleted alarm: {alarm_id}")
        except Exception as e:
            print(f"Failed to delete alarm {alarm_id}: {e}")


    # Updating save_alarm_time to accept prefix
    def save_alarm_time(self, alarm_id, alarm_time, prefix):
        self.save_time_to_file(alarm_id, alarm_time, prefix=prefix)
        print(f"Alarm time saved: {alarm_time}")

    # Adjusting method signature for save_time_to_file
    def save_time_to_file(self, time_id, time_data, prefix):
        """
        Save time data to a file with the specified prefix.
        """
        filename = f"{prefix}{time_id}.txt"
        try:
            with open(filename, 'w') as file:
                file.write(f"{time_data['hour']:02d}\n")
                file.write(f"{time_data['minute']:02d}\n")
                file.write(f"{time_data['second']:02d}\n")
            print(f"Time saved to {filename}: {time_data}")
        except Exception as e:
            print(f"Failed to save time to {filename}: {e}")

    def new_alarm(self, alarm_time):
        """
        Create a new alarm with a unique ID and save the alarm time to a file.
        """
        alarm_id = self.new_id()
        self.save_time_to_file(alarm_id, alarm_time, prefix=self.ALARM_FILE_PREFIX)
        return alarm_id

    def new_snooze(self, snooze_minutes):
        """
        Create a new snooze with a unique ID and save the snooze time to a file.
        """
        current_time = self.rtc.datetime()
        snooze_time = {
            "hour": (current_time[4] + (current_time[5] + snooze_minutes) // 60) % 24,
            "minute": (current_time[5] + snooze_minutes) % 60,
            "second": current_time[6]
        }
        snooze_id = self.new_id()
        self.save_time_to_file(snooze_id, snooze_time, prefix=self.SNOOZE_FILE_PREFIX)
        print(f"IN NEW_SNOOZE: {snooze_time}")
        return snooze_id, snooze_time
    
    def new_id(self):
        """
        Generate a new ID using a random number.
        """
        return str(random.randint(100000, 999999))

    def load_time(self, alarm_id, prefix):
        try:
            with open(f"{prefix}{alarm_id}.txt", 'r') as file:
                lines = file.readlines()
                if len(lines) >= 3:
                    return {
                        "hour": int(lines[0].strip()),
                        "minute": int(lines[1].strip()),
                        "second": int(lines[2].strip())
                    }
        except Exception as e:
            print(f"Failed to read {prefix}{alarm_id}.txt: {e}")
        return None

    def get_alarm_time(self, alarm_id):
        return self.load_time(alarm_id, prefix=ALARM_FILE_PREFIX)

    def get_all_alarm_times(self):
        alarms = self.get_alarm_times()
        snoozes = self.get_snooze_time()
        #print(f"snoozes: {snoozes}")
        #print(f"alarms: {alarms}")
        return alarms + snoozes

    def get_snooze_time(self):
        """
        Scan for all snooze files and return a list of tuples (snooze_id, time).
        Raises an error if more than one snooze file is found.
        """
        snooze_times = []
        for filename in uos.listdir():
            if filename.startswith(self.SNOOZE_FILE_PREFIX):
                snooze_id = filename[len(self.SNOOZE_FILE_PREFIX):-4]  # Remove prefix and .txt suffix
                snooze_time = self.load_time(snooze_id, prefix=self.SNOOZE_FILE_PREFIX)
                if snooze_time:
                    snooze_times.append((snooze_id, snooze_time))
                    
        if len(snooze_times) > 1:
            raise Exception("More than one snooze file found")
        return snooze_times if snooze_times else []
    
    def get_alarm_times(self):
        """
        Scan for all alarm files and return a list of tuples (alarm_id, time).
        """
        alarm_times = []
        for filename in uos.listdir():
            if filename.startswith(self.ALARM_FILE_PREFIX) and filename.endswith(self.ALARM_FILE_SUFFIX):
                alarm_id = filename[len(self.ALARM_FILE_PREFIX):-len(self.ALARM_FILE_SUFFIX)]
                alarm_time = self.load_time(alarm_id, prefix=self.ALARM_FILE_PREFIX)
                if alarm_time:
                    alarm_times.append((alarm_id, alarm_time))
        return alarm_times

    def format_datetime(self, datetime):
        try:
            year, month, day, weekday, hour, minute, second, *_ = datetime  # Use * to handle additional values

            if self.is_12_hour:
                hour, am_pm = self.convert_to_12_hour(hour)
                time = '{:02d}:{:02d}:{:02d} {}'.format(hour, minute, second, am_pm)
            else:
                time = '{:02d}:{:02d}:{:02d}'.format(hour, minute, second)

            date = '{:04d}-{:02d}-{:02d}'.format(year, month, day)
            weekday_str = self.reverse_weekday_map.get(weekday, "Invalid weekday")

            return {
                "time": time,
                "date": date,
                "year": year,
                "month": month,
                "day": day,
                "weekday": weekday_str,
                "hour": hour,
                "minute": minute,
                "second": second
            }
        except Exception as e:
            # TODO: implement custom exceptions and logging
            print(f"error in format_datetime: {e}")
            raise

    def get_formatted_datetime_from_module(self):
        """
        Get the current datetime data via i2c. If an interrupt handling operation
        takes a long time (menu transitions), then we might see an i2c
        timeout issue here as a result. Assume the interrupt handling has higher
        priority, ignore the error, and get the time on the next cycle.
        """
        try:
            return self.format_datetime(self.rtc.datetime())
        except OSError as e:
            # Return null values on [Errno 110] ETIMEDOUT
            print(f"Error fetching datetime: {e}")
            return {
                "time": "00:00:00",
                "date": "0000-00-00",
                "year": 0,
                "month": 0,
                "day": 0,
                "weekday": "sunday",
                "hour": 0,
                "minute": 0,
                "second": 0
            }

    def file_exists(self, filepath):
        try:
            uos.stat(filepath)
            return True
        except OSError:
            return False

    def delete_all_snooze_files(self):
        files = uos.listdir()
        for file in files:
            if file.startswith(self.SNOOZE_FILE_PREFIX):
                try:
                    uos.remove(file)
                    print(f"Deleted snooze file: {file}")
                except Exception as e:
                    print(f"Failed to delete snooze file: {file}\n{e}")
    

if __name__ == "__main__":
    # Initialize I2C0
    i2c = machine.I2C(0, sda=machine.Pin(16), scl=machine.Pin(17))

    # Initialize DS1307
    rtc = DS1307(i2c)

    # Set the time (year, month, day, weekday, hour, minute, second)
    # This only needs to be done once if the RTC has a battery
    rtc.datetime((2024, 7, 4, 4, 12, 0, 0))  # year, month, day, weekday, hour, minute, second

    # Get the time
    while True:
        datetime = rtc.datetime()
        print('Raw datetime:', datetime)
        year, month, day, weekday, hour, minute, second, *_ = datetime  # Use * to handle add
