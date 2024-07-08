import machine
import utime
from ds1307 import DS1307

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
    print('Date: {:04d}-{:02d}-{:02d}'.format(year, month, day))
    print('Time: {:02d}:{:02d}:{:02d}'.format(hour, minute, second))
    utime.sleep(1)
