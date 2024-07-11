import machine
import utime
from ds1307 import DS1307

class RTC:
        
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
        self.use_24_hour_format = True

        # Set the time (year, month, day, weekday, hour, minute, second)
        current_time = self.rtc.datetime()
        print(f"Loaded RTC. Time: {current_time}")

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

    def get_datetime(self):
        """
        Get the current datetime data via i2c. If an interrupt handling operation
        takes a long time (cough cough menu transitions), then we might see an i2c
        timeout issue here as a result. Assume the interrupt handling has higher
        priority, ignore the error, and get the time on the next cycle.
        """
        try:
            datetime = self.rtc.datetime()
            year, month, day, weekday, hour, minute, second, *_ = datetime  # Use * to handle additional values
            date = '{:04d}-{:02d}-{:02d}'.format(year, month, day)
            time = '{:02d}:{:02d}:{:02d}'.format(hour, minute, second)
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
        year, month, day, weekday, hour, minute, second, *_ = datetime  # Use * to handle additional values
        print("{weekday}")
        print("Date: {:04d}-{:02d}-{:02d}".format(year, month, day))
        print("Time: {:02d}:{:02d}:{:02d}".format(hour, minute, second))
        utime.sleep(1)
