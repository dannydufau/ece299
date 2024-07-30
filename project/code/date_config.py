from ui import UI
from encoder import RotaryEncoder
from context_queue import context_queue
from context import Context


class DateConfig(UI):
    def __init__(self, display, rtc, encoder_pins, led_pin, id):
        self.display = display
        #self.radio_control = radio_control
        self.id = id
        self.rtc = rtc
        #self.current_frequency = self.radio_control.get_frequency()  # Get current frequency
        
        # Load context
        self.ui_context = self.load_context()
        self.header = self.ui_context.get("header")
        self.min = self.ui_context.get("min", 2020)  # Default min year should be 1970
        self.max = self.ui_context.get("max", 2030)  # Default max year if setting year
        if self.header == "month":
            self.min = 1
            self.max = 12
        elif self.header == "day":
            self.min = 1
            self.max = 31  # Simplification; actual max will depend on month/year
        self.current_value = self.min

        self.selected_index = None
        self.selected_item = None

        print(f"IN date_config: {self.header}")

        try:
            self.encoder = RotaryEncoder(
                pin_a=encoder_pins[0],
                pin_b=encoder_pins[1],
                pin_switch=encoder_pins[2],
                led_pin=led_pin,
                rollover=True,
                max=self.max,
                min=self.min,
                button_callback=self.button_release, # method called here on button click
                on_release=True # tell button class to respond to release
            )

        except Exception as e:
            print("ENCODER NOT CREATED FOR date_CONFIG")
            raise

        self.update_display()

    def load_context(self):
        """
        Dequeue context from the queue and return the ui_context.
        """
        context = context_queue.dequeue()
        print(f"frequency_config,load_context,dequeue\n{context.router_context}\n{context.ui_context}\n{context_queue.size()}")

        if isinstance(context, Context):
            return context.ui_context

        return context if context else {}

    def update_display(self):
        self.display.clear()
        self.display.update_text(self.header, 0, 0)
        self.display.update_text(str(self.current_value), 0, 1)

    def poll_selection_change_and_update_display(self):
        new_value, direction = self.encoder.get_counter()
        if new_value != self.current_value:
            self.current_value = new_value
            self.update_display()

    def button_release(self):
        self.write_date_to_rtc()
        self.build_context()
        return self.ui_context
    
    def write_date_to_rtc(self):
        """
        Description: Sets the date. Writes the date metric stored in current_value to
        the RTC module.
        """
        try:
            current_datetime = self.rtc.rtc.datetime()
            new_year = current_datetime[0]
            new_month = current_datetime[1]
            new_day = current_datetime[2]
            new_hour = current_datetime[4]
            new_minute = current_datetime[5]
            new_second = current_datetime[6]
            new_weekday = current_datetime[3]
            
            # Determine which metric to update depending on the header
            if self.header == "year":
                new_year = int(self.current_value)
            elif self.header == "month":
                new_month = int(self.current_value)
            elif self.header == "day":
                new_day = int(self.current_value)
        
            # Update the RTC module
            self.rtc.set_datetime(new_year,
                                  new_month,
                                  new_day,
                                  new_weekday,
                                  new_hour,
                                  new_minute,
                                  new_second)

            current_datetime = self.rtc.get_formatted_datetime_from_module()
            print(f"after formatted: {current_datetime}")
            
        except Exception as e:
            print(f"DateConfig.write_date_to_rtc Failed setting the date and time directly.\n{e}")

        # Reset the encoder counter after writing the date
        self.encoder.reset_counter()
    
    def button_releaseNOPE(self):
        if self.header == "integer_part":
            self.current_frequency = float(f"{self.current_value}.0")
            self.radio_control.set_frequency(self.current_frequency)
            self.build_context("fractional_part", "frequency_fractional", 0, 9)
        elif self.header == "fractional_part":
            new_frequency = float(f"{int(self.current_frequency)}.{self.current_value}")
            self.radio_control.set_frequency(new_frequency)
            self.build_context("Main Menu", "main_menu", None, None)
        print(f"current_frequency: {self.radio_control.get_frequency()}")
            
        return self.ui_context

    def build_context(self):
        next_header = None
        next_ui_id = "set_date"
        min = None
        max = None
        if self.header == "year":
            next_header = "month"
            min = 1
            max = 12
        elif self.header == "month":
            next_header = "day"
            min = 1
            max = 31
        elif self.header == "day":
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
            return True
        return False

    def stop(self):
        if self.encoder:
            self.encoder.pin_a.irq(handler=None)
            self.encoder.pin_b.irq(handler=None)
            self.encoder.button.disable_irq()
        if self.display:
            self.display.clear()

