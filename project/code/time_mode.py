import uos
from machine import Pin, Timer
from display import CR_SPI_Display
from encoder import RotaryEncoder
from ui import UI
from context_queue import context_queue
from context import Context


class TimeMode(UI):
    CONFIG_FILE = "time_mode_config.txt"

    def __init__(self, display, rtc, encoder_pins, led_pin, header):
        self.display = display
        self.rtc = rtc
        self.header = header
        self.ui_context = self.load_context()
        #self.next_config = None
        self.current_mode = self.load_time_mode()
        self.update_display()

        # Create an instance of the RotaryEncoder
        self.encoder = RotaryEncoder(
            pin_a=encoder_pins[0],
            pin_b=encoder_pins[1],
            pin_switch=encoder_pins[2],
            led_pin=led_pin,
            rollover=True,
            max=1,
            min=0,
            button_callback=self.button_release, # method called here on button click
            on_release=True # tell button class to respond to release
        )

    def load_context(self):
        """
        Dequeue context from the queue and return the ui_context.
        """
        context = context_queue.dequeue()
        print(f"alarm_config,load_context,dequeue\n{context.router_context}\n{context.ui_context}\n{context_queue.size()}")

        if isinstance(context, Context):
            return context.ui_context

        return context if context else {}

    def update_display(self):
        self.display.clear()
        self.display.update_text(self.header, 0, 0)
        mode_text = "12-hour" if self.current_mode == 0 else "24-hour"
        self.display.update_text(mode_text, 0, 1)

    def poll_selection_change_and_update_display(self):
        new_mode, direction = self.encoder.get_counter()
        if new_mode != self.current_mode:
            self.current_mode = new_mode
            self.update_display()

    def is_encoder_button_pressed(self):
        if self.encoder.get_button_state():
            self.select_action()
            return True
        return False
        #return self.encoder.get_button_state()

    def reset(self):
        self.current_mode = 0  # Default to 12-hour mode
        self.update_display()

    def stop(self):
        self.encoder.pin_a.irq(handler=None)
        self.encoder.pin_b.irq(handler=None)
        self.encoder.button.disable_irq()

    def button_release(self):
        # Reset the encoder counter
        self.encoder.reset_counter()
        # Explicitly call update display
        #self.update_display()
        self.set_time_mode()
        self.build_context()

    def build_context(self):
        # After setting the time mode, return to the main menu
        context = Context(
            router_context={"next_ui_id": "main_menu"},
            ui_context={
                "header": "Main Menu",
                "selectables": [
                    {"display_text": "Time", "id": "time_menu"},
                    {"display_text": "Radio", "id": "radio_menu"}
                ]
            }
        )
        context_queue.add_to_queue(context)
    
    def set_time_mode(self):
        print(f"Setting time mode to selected: {self.current_mode}")
        # Sets the rtc instance directly here.  Maybe rethink this in std queue op
        self.rtc.is_12_hour = (self.current_mode == 0)
        self.save_time_mode()
        print(f"Time mode set to: {'12-hour' if self.rtc.is_12_hour else '24-hour'}")

    def save_time_mode(self):
        with open(self.CONFIG_FILE, 'w') as file:
            file.write(str(self.current_mode))
        print(f"Time mode {self.current_mode} saved to {self.CONFIG_FILE}")

    def load_time_mode(self):
        try:
            if self.file_exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, 'r') as file:
                    mode = int(file.read().strip())
                    print(f"Time mode {mode} loaded from {self.CONFIG_FILE}")
                    return mode
        except Exception as e:
            print(f"Failed to load time mode. Defaulting to 24-hour mode. Error: {e}")
        return 1  # Default to 24-hour mode if loading fails

    def file_exists(self, filepath):
        try:
            uos.stat(filepath)
            return True
        except OSError:
            return False
