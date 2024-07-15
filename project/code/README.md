Issues to discuss:

Deploy notes:

rshell
connect serial /dev/ttyACM0
cp /pyboard/main.py .
cp main.py /pyboard/
ls /pyboard
exit


##
talk about max_recursion (code saved in dir)

i2c timeout getting rtc data, likely do to 'long' interrupt handling
on menu transition.  isp are too long :(

    def get_datetime(self):
        """
        Get the current datetime data via i2c.  If an interrupt handling operation
        takes a long time (cough cough menu transitions), then we might see an i2c
        timeout issue here as a result.  Assume the interrupt handling has higher
        priority, ignore the error, and get the time on the next cycle.
        """
        try:
            datetime = self.rtc.datetime()
            year, month, day, weekday, hour, minute, second, *_ = datetime  # Use * to handle additional values
            date = '{:04d}-{:02d}-{:02d}'.format(year, month, day)
            time = '{:02d}:{:02d}:{:02d}'.format(hour, minute, second)
            
            return {
                "time": time,
                "date": date,
                "year": year,
                "month": month,
                "day": day,
                "weekday": weekday,
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
                "weekday": 0,
                "hour": 0,
                "minute": 0,
                "second": 0
            }