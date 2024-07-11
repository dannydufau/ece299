from machine import Pin, Timer
from display import CR_SPI_Display
from encoder import RotaryEncoder
import time
import sys
from config import Config
from ui import UI

class TimeConfig(UI):
    def __init__(
        self,
        display,
        rtc,
        encoder_pins,
        led_pin,
        header,
        min=0,
        max=60,
        next_config=None
    ):
        self.display = display
        self.rtc = rtc
        self.header = header
        self.next_config = next_config
        self.current_value = 0
        self.update_display()

        # Create an instance of the RotaryEncoder
        self.encoder = RotaryEncoder(
            pin_a=encoder_pins[0], 
            pin_b=encoder_pins[1], 
            pin_switch=encoder_pins[2], 
            led_pin=led_pin, 
            rollover=True, 
            max=max, 
            min=min
        )

    def update_display(self):
        self.display.clear()
        self.display.update_text(self.header, 0, 0)
        self.display.update_text(str(self.current_value), 0, 1)

    def poll_selection_change_and_update_display(self):
        new_value, direction = self.encoder.get_counter()
        if new_value != self.current_value:
            self.current_value = new_value
            self.update_display()

    def get_selection(self):
        print("get_selection called")
        if self.is_encoder_button_pressed():
            self.write_time_to_rtc()
            if self.next_config:
                
                # Reset the encoder counter
                self.encoder.reset_counter()
                
                # Explicitly call update display
                self.update_display()
                return self.next_config
        return {"id": "main_menu", "display_text": "Main Menu"}

    def is_encoder_button_pressed(self):
        return self.encoder.get_button_state()

    def reset(self):
        self.current_value = 0
        self.update_display()

    def stop(self):
        self.encoder.pin_a.irq(handler=None)
        self.encoder.pin_b.irq(handler=None)
        self.encoder.button.disable_irq()

    def write_time_to_rtc(self):
        print("write rtc called")
        current_datetime = self.rtc.get_datetime()
        
        new_hour = int(current_datetime["hour"])
        new_minute = int(current_datetime["minute"])
        new_second = int(current_datetime["second"])
        new_weekday = self.rtc.weekday_map[current_datetime["weekday"].lower()]
        
        if self.header == "Hour":
            print(f"Setting hour: {self.current_value}")
            new_hour = int(self.current_value)
        elif self.header == "Minute":
            print(f"Setting minute: {self.current_value}")
            new_minute = int(self.current_value)
        elif self.header == "Second":
            print(f"Setting second: {self.current_value}")
            new_second = int(self.current_value)
        
        print(f"Writing to RTC -> Year: {current_datetime['year']}, Month: {current_datetime['month']}, Day: {current_datetime['day']}, Weekday: {new_weekday}, Hour: {new_hour}, Minute: {new_minute}, Second: {new_second}")
        
        # Directly call rtc.rtc.datetime()
        try:
            self.rtc.rtc.datetime((int(current_datetime["year"]),
                                   int(current_datetime["month"]),
                                   int(current_datetime["day"]),
                                   new_weekday,
                                   new_hour,
                                   new_minute,
                                   new_second))
        except Exception as e:
            print(f"Failed setting the date and time directly.\n{e}")

        # Reset the encoder counter after writing the time
        self.encoder.reset_counter()
