import machine
import utime
import time
import uos
import random
from ds1307 import DS1307
from square_wave_generator import SquareWaveGenerator
from logger import Logger


class RealTimeClock:
    CONFIG_FILE = "time_mode_config.txt"
    TIMEZONE_FILE = "timezone_config.txt" 
    SNOOZE_FILE_PREFIX = "snooze_"
    ALARM_FILE_PREFIX = "alarm_"
    ALARM_FILE_SUFFIX = ".txt"

    def __init__(self):

        # Initialize the logger
        self.logger = Logger(level=Logger.INFO)
        
        self.battery_pin = machine.ADC(28)  # Initialize ADC on pin 28
        
        self.weekday_map = {
            "sunday": 0,
            "monday": 1,
            "tuesday": 2,
            "wednesday": 3,
            "thursday": 4,
            "friday": 5,
            "saturday": 6
        }

        # Timezone offsets
        self.tz_map = {
            "UTC": 0,
            "CST": -6,  # Mexico City
            "CDT": -5,  # Mexico City Daylight Time
            "PST": -8,
        }
        
        self.reverse_weekday_map = {v: k for k, v in self.weekday_map.items()}

        # Initialize I2C0
        i2c = machine.I2C(0, sda=machine.Pin(16), scl=machine.Pin(17))

        # Initialize DS1307
        self.rtc = DS1307(i2c)
        
        # Load time mode configuration
        self.is_12_hour = self.load_time_mode() == 0

        # Load timezone from file
        self.timezone = self.load_timezone()
        
        # Set the time (year, month, day, weekday, hour, minute, second)
        current_time = self.rtc.datetime()
        self.logger.info(f"Loaded RTC. Time: {current_time}")
        
        # Create alarm sound instances
        self.alarm = SquareWaveGenerator(22, 888)  # GP22, 1 kHz frequency

        # Initialize alarm active flag
        self.alarm_active = None
        self.alarm_off()
        
        self.lock = False

    def read_battery_voltage(self):
        adc_value = self.battery_pin.read_u16()  # Read ADC value (0-65535)
        voltage = adc_value * 3.3 / 65535  # Convert to voltage (assuming a 3.3V reference)
        return voltage

    def get_battery_status(self):
        voltage = self.read_battery_voltage()
        print(f"Battery voltage: {voltage:.2f}V")

        if voltage < 2.0:
            return "Battery low"
        elif voltage < 2.5:
            return "Battery medium"
        else:
            return "Battery high"

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

    def load_time_mode(self):
        try:
            if self.file_exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, 'r') as file:
                    mode = int(file.read().strip())
                    self.logger.debug(f"Time mode {mode} loaded from {self.CONFIG_FILE}")
                    return mode
            else:
                # Create the file with default 24-hour mode
                with open(self.CONFIG_FILE, 'w') as file:
                    file.write('1')
                return 1

        except Exception as e:
            msg = "Error in rtc.load_time_mode loading time mode from file, setting to 24h mode"
            self.logger.error(e, msg)
            return 1  # Default to 24-hour mode if loading fails

    def load_timezone(self):
        try:
            if self.file_exists(self.TIMEZONE_FILE):
                with open(self.TIMEZONE_FILE, 'r') as file:
                    timezone = file.read().strip()
                    self.logger.debug(f"Timezone {timezone} loaded from {self.TIMEZONE_FILE}")
                    return timezone
            else:
                # Create the file with default timezone 'PST'
                with open(self.TIMEZONE_FILE, 'w') as file:
                    file.write('PST')
                return 'PST'

        except Exception as e:
            msg = "Error in rtc.load_timezone loading timezone from file, setting to default PST"
            self.logger.error(e, msg)
            return 'PST'  # Default to PST if loading fails

    def find_alarm_by_time(self, alarm):
        """
        Find the alarm ID by time. Return None if no match is found.
        """
        for alarm_id, alarm_time in self.get_all_alarm_times():  # Use get_all_alarm_times to include snoozes
            #self.logger.debug(f"FIND: alarm_time: {alarm_time}, alarm: {alarm}")
            if (alarm_time['hour'] == alarm['hour'] and
                alarm_time['minute'] == alarm['minute'] and
                alarm_time['second'] == alarm['second']):
                return alarm_id
        return None
    
    def delete_alarm(self, alarm_id):
        """
        Delete the alarm file corresponding to the given alarm ID.
        """
        print("IN rtc.delete_alarm")
        alarm_file = f"{self.ALARM_FILE_PREFIX}{alarm_id}{self.ALARM_FILE_SUFFIX}"
        try:
            if self.file_exists(alarm_file):
                print("AFTER file_Exists")
                uos.remove(alarm_file)
                # recursion
                #self.logger.info(f"Deleted alarm: {alarm_id}")

        except Exception as e:
            msg = f"Error in rtc.delete_alarm while deleting alarm {alarm_id}"
            print(f"{msg}\n{e}")
            # max recursion depth
            #self.logger.error(e, msg)

    def save_alarm_timeNOTUSING(self, alarm_id, alarm_time, prefix):
        # max recursion
        self.save_time_to_file(alarm_id, alarm_time, prefix=prefix)
        self.logger.info(f"Alarm time saved: {alarm_time}")

    def save_time_to_file(self, time_id, time_data, prefix):
        """
        Save alarm time data to a file with the specified prefix.
        """
        filename = f"{prefix}{time_id}.txt"
        try:
            with open(filename, 'w') as file:
                file.write(f"{time_data['hour']:02d}\n")
                file.write(f"{time_data['minute']:02d}\n")
                file.write(f"{time_data['second']:02d}\n")
            self.logger.debug(f"Time saved to {filename}: {time_data}")

        except Exception as e:
            msg = f"Error in save_time_to_file saving {filename}"
            self.logger.error(e, msg)

    def new_alarmNOTUSING(self, alarm_time):
        """
        NOTE: can't use due to max recursion depth
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
        return snooze_id, snooze_time
    
    def new_id(self):
        """
        Generate a new ID using a random number.
        """
        return str(random.randint(100000, 999999))

    def load_time(self, alarm_id, prefix):
        """
        load alarm time data from file
        """
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
            msg = "Error in rtc.load_time reading {prefix}{alarm_id}.txt"
            self.logger.error(e, msg)

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

    def convert_to_12_hour(self, hour):
        # NOTE: save in time_mode config - consider changing
        if hour == 0:
            return 12, 'AM'
        elif hour == 12:
            return 12, 'PM'
        elif hour > 12:
            return hour - 12, 'PM'
        else:
            return hour, 'AM'

    def convert_timezone(self, datetime_tuple, desired_tz):
        """
        Convert the given datetime to the desired timezone.
        """
        # NOTE: save in tz_config - consider changing
        # Recursion error.. cant do this here
        current_tz = self.load_timezone()

        if current_tz != desired_tz:
            # Extract the current datetime components
            year, month, day, weekday, hour, minute, second, *_ = datetime_tuple
            
            # Calculate current timestamp in seconds
            timestamp = utime.mktime((year, month, day, hour, minute, second, weekday, 0))
            
            # Get timezone offsets in seconds
            current_offset = self.tz_map.get(current_tz, 0) * 3600
            desired_offset = self.tz_map.get(desired_tz, 0) * 3600
            
            # Calculate the new timestamp
            new_timestamp = timestamp - current_offset + desired_offset
            
            # Convert the new timestamp back to a datetime tuple
            new_datetime_tuple = utime.localtime(new_timestamp)[:7]
            
            return new_datetime_tuple, desired_tz
        return datetime_tuple, current_tz

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
            #self.logger.info(f"RTC datetime set to: {self.rtc.datetime()}")  # Confirm setting time
            print(f"RTC datetime set to: {self.rtc.datetime()}")            

        except Exception as e:
            msg = f"Error in rtc set_datetime setting date and time.\n{e}"
            #self.logger.error(e, msg)
            print(f"set_datetime: {msg}")

    #def format_datetime(self, datetime_tuple):
    def format_datetimeNOTUSING(self, datetime_tuple, current_tz):
        # CAUSES MAX RECURSION
        try:
            #current_tz = self.load_timezone() # CANT DO THIS DUE TO MAX DEPTH
            year, month, day, weekday, hour, minute, second, *_ = datetime_tuple  # Use * to handle additional values
            # print(f"hour: {hour} minute: {minute} second: {second}")
            
            # Ensure month and day are set correctly if they are zero
            if month == 0:
                month = 1
            if day == 0:
                day = 1

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
                "second": second,
                "timezone": current_tz#self.timezone,
            }

        except Exception as e:
            msg = "Error in rtc.format_datetime"
            print(f"{msg}\n{e}")


    def get_formatted_datetime_from_module(self):
        """
        Get the current datetime data via i2c. If an interrupt handling operation
        takes a long time (menu transitions), then we might see an i2c
        timeout issue here as a result. Assume the interrupt handling has higher
        priority, ignore the error, and get the time on the next cycle.
        """
        try:
            current_tz = self.load_timezone()
            datetime_raw = self.rtc.datetime()
            #print(f"RAW: {datetime_raw}")
            #return self.format_datetime(datetime_raw, current_tz)
            year, month, day, weekday, hour, minute, second, *_ = datetime_raw  # Use * to handle additional values
            # print(f"hour: {hour} minute: {minute} second: {second}")
            
            # Ensure month and day are set correctly if they are zero
            if month == 0:
                month = 1
            if day == 0:
                day = 1

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
                "second": second,
                "timezone": current_tz#self.timezone,
            }
        except Exception as e:
            # Print and retry
            msg = f"IGNORE - THIS RECOVERS ITSELF. Error fetching datetime: {e}"
            print(msg)

        # If all retries fail, return null values
        return {
            "time": "00:00:00",
            "date": "0000-00-00",
            "year": 0,
            "month": 0,
            "day": 0,
            "weekday": "sunday",
            "hour": 0,
            "minute": 0,
            "second": 0,
            "timezone": "*"
        }

    def file_exists(self, filepath):
        try:
            uos.stat(filepath)
            return True

        except OSError as e:
            msg = f"Error in rtc.file_exists while check path name: {filepath}"
            self.logger.error(msg, e)
            return False

    def delete_all_snooze_files(self):
        files = uos.listdir()
        for file in files:
            if file.startswith(self.SNOOZE_FILE_PREFIX):
                try:
                    uos.remove(file)
                    print(f"Deleted snooze file: {file}")
                    # Recursion
                    #self.logger.info(f"Deleted snooze file: {file}")

                except Exception as e:
                    msg = f"Error in rtc.delete_all_snooze_Files while deleting snooze file: {file}"
                    self.logger.error(e, msg)

    def sync_system_time(self):
        try:
            current_time = self.rtc.datetime()
            # The format for the tuple is (year, month, mday, hour, minute, second, weekday, yearday)
            system_time = (current_time[0], current_time[1], current_time[2], current_time[4], current_time[5], current_time[6], current_time[3], 0)
            machine.RTC().datetime(system_time)
            self.logger.info(f"System time synchronized with RTC: {system_time}")
        
        except Exception as e:
            msg = f"Error in rtc.sync_system_time while syncing module to sys time"
            self.logger.error(e, msg)
        
    def test_setting_datetime(self):
        try:
            current_time = self.rtc.datetime()
            print(f"RTC current datetime: {current_time}")
            if current_time[0] == 2000:
                # If RTC time is the default (after power loss), set it to a known time
                print("RTC time is default. Setting to known time.")
                self.set_datetime(2024, 1, 1, 0, 0, 0, 0)
        except Exception as e:
            msg = f"Error in initialize_rtc getting RTC datetime.\n{e}"
            print(f"initialize_rtc: {msg}")
            self.logger.error(e, msg)

    def test_battery(self):
        # Check battery status
        battery_status = rtc.get_battery_status()
        print(f"Battery status: {battery_status}")

if __name__ == "__main__":
    
    rtc = RealTimeClock()

    rtc.test_battery()

    '''
    # test update time
    before = rtc.get_formatted_datetime_from_module()
    print(f"before: {before}")
    
    # Set the RTC time
    rtc.set_datetime(2024, 7, 13, "saturday", 12, 3, 0)  # Example: 12th July 2024, Friday, 12:03:00

    after = rtc.get_formatted_datetime_from_module()
    print(f"after: {after}")
    
    # test sync to system clock
    # Print current system time to verify it was updated
    current_time = utime.localtime()
    print(f"Current system time BEFORE sync: {current_time}")

    # Set the RTC time
    rtc.set_datetime(2024, 7, 12, "friday", 12, 0, 0)  # Example: 12th July 2024, Friday, 12:00:00
    
    # Sync system time with RTC
    rtc.sync_system_time()
    
    # Print current system time to verify it was updated
    current_time = utime.localtime()
    print(f"Current system time AFTER sync: {current_time}")
    
    # Test timezone conversion
    test_datetime = (2024, 7, 13, 5, 12, 0, 0)  # Example datetime
    new_datetime, new_tz = rtc.convert_timezone(test_datetime, "CST")
    print(f"Converted datetime: {new_datetime} to timezone: {new_tz}")
    '''
