from machine import Pin, Timer
from display import CR_SPI_Display
from encoder import RotaryEncoder
import time
import sys
import uos
from ui import UI
from context_queue import context_queue
from context import Context


class TimeConfig(UI):
    def __init__(self, display, rtc, encoder_pins, led_pin):
        self.display = display
        self.rtc = rtc
        self.encoder_pins = encoder_pins
        self.led_pin = led_pin

        # Load context and populate properties
        self.ui_context = self.load_context()
        
        # Default to "hour" if not provided
        self.header = self.ui_context.get("header", "hour")
        self.min = self.ui_context.get("min", 0)
        self.max = self.ui_context.get("max", 23) if self.header == "hour" else 59
        self.current_value = self.min
        
        # Initialize the encoder
        try:
            self.encoder = RotaryEncoder(
                pin_a=encoder_pins[0], 
                pin_b=encoder_pins[1], 
                pin_switch=encoder_pins[2], 
                led_pin=led_pin, 
                rollover=True,
                max=self.max,
                min=self.min
            )
        except Exception as e:
            sys.print_exception(e)
            print("ENCODER NOT CREATED FOR TIME CONFIG")
            raise

        # Initialize other components and state as needed
        self.update_display()

    def load_context(self):
        """
        Dequeue context from the queue and return the ui_context.
        """
        context = context_queue.dequeue()
        print(f"time_config,load_context,dequeue\n{context.router_context}\n{context.ui_context}\n{context_queue.size()}")

        if isinstance(context, Context):
            return context.ui_context

        return context if context else {}

    def update_display(self):
        """
        Update the display on encoder changes
        """
        self.display.clear()
        self.display.update_text(self.header, 0, 0)
        self.display.update_text(str(self.current_value), 0, 1)

    def poll_selection_change_and_update_display(self):
        """
        Detect if the encoder input has changed
        """
        new_value, direction = self.encoder.get_counter()
        if new_value != self.current_value:
            self.current_value = new_value
            self.update_display()

    def select_action(self):
        self.write_time_to_rtc()
        self.build_context()
        return self.ui_context

    def build_context(self):
        next_header = None
        next_ui_id = "set_time"
        min = None
        max = None
        if self.header == "hour":
            next_header = "minute"
            min = 0
            max = 59
        elif self.header == "minute":
            next_header = "second"
            min = 0
            max = 59
        elif self.header == "second":
            next_ui_id = "main_menu"
            next_header = ""
        
        ui_context = {
            "header": next_header,
            "min": min,
            "max": max
        }
        router_context = {"next_ui_id": next_ui_id}
        context_queue.add_to_queue(Context(router_context=router_context, ui_context=ui_context))

    def is_encoder_button_pressed(self):
        if self.encoder.get_button_state():
            self.select_action()
            return True
        return False

    def reset(self):
        self.current_value = self.min
        self.update_display()

    def stop(self):
        if self.encoder:
            self.encoder.pin_a.irq(handler=None)
            self.encoder.pin_b.irq(handler=None)
            self.encoder.button.disable_irq()
        if self.display:
            self.display.clear()

    def write_time_to_rtc(self):
        """
        Description: Sets the time. Writes the time metric stored in current_value to
        the RTC module.
        """
        # Read the current datetime the module is configured to
        current_datetime = self.rtc.get_formatted_datetime_from_module()
        
        new_hour = int(current_datetime["hour"])
        new_minute = int(current_datetime["minute"])
        new_second = int(current_datetime["second"])
        new_weekday = self.rtc.weekday_map[current_datetime["weekday"].lower()]
        
        # Determine which metric to update depending on the header
        if self.header == "hour":
            new_hour = int(self.current_value)
        elif self.header == "minute":
            new_minute = int(self.current_value)
        elif self.header == "second":
            new_second = int(self.current_value)
        
        # Update the RTC module
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
