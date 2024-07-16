from machine import Pin, Timer
from display import CR_SPI_Display
from encoder import RotaryEncoder
import time
import sys
import uos
from ui import UI


class AlarmDisable(UI):
    def __init__(
        self,
        display,
        rtc,
        encoder_pins,
        led_pin,
        header="Disable Alarm",
        min=0,
        max=1,
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

    #def get_selection(self):
    def get_context(self):
        """
        If the encoder button is pressed, perform duties
        associated with the selected item and return the
        next menu.
        """
        if self.is_encoder_button_pressed():
            self.disable_alarm()
            if self.next_config:
                self.encoder.reset_counter()
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

    def disable_alarm(self):
        """
        Disable the alarm in the RTC module.
        """
        self.rtc.alarm_off()
        self.encoder.reset_counter()
