import uos
from machine import Pin, Timer
from display import CR_SPI_Display
from encoder import RotaryEncoder
from ui import UI


class TimeMode(UI):
    CONFIG_FILE = "time_mode_config.txt"

    def __init__(self, display, rtc, encoder_pins, led_pin, header, next_config):
        self.display = display
        self.rtc = rtc
        self.header = header
        self.next_config = next_config
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
            min=0
        )

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

    def get_context(self):
    #def get_selection(self):
        print("get_selection called")
        if self.is_encoder_button_pressed():
            self.set_time_mode()
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
        self.current_mode = 0  # Default to 12-hour mode
        self.update_display()

    def stop(self):
        self.encoder.pin_a.irq(handler=None)
        self.encoder.pin_b.irq(handler=None)
        self.encoder.button.disable_irq()

    def set_time_mode(self):
        print("Setting time mode")
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
