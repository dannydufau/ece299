from machine import Pin, Timer
from display import CR_SPI_Display
from encoder import RotaryEncoder
import time
import sys
import uos
from ui import UI
from context_queue import context_queue
from context import Context


class AlarmDisable(UI):
    def __init__(self, display, rtc, encoder_pins, led_pin):
        self.display = display
        self.rtc = rtc
        self.encoder_pins = encoder_pins
        self.led_pin = led_pin

        # Load context and populate properties
        self.ui_context = self.load_context()

        # Default to "Disable Alarm" if not provided
        self.header = self.ui_context.get("header", "Turn off Alarm?")
        self.min = self.ui_context.get("min", 0)
        self.max = self.ui_context.get("max", 1)

        # hardcode this for now
        self.current_value = 1  # self.min

        # Initialize the encoder
        try:
            self.encoder = RotaryEncoder(
                pin_a=encoder_pins[0],
                pin_b=encoder_pins[1],
                pin_switch=encoder_pins[2],
                led_pin=led_pin,
                rollover=True,
                max=self.max,
                min=self.min,
                button_callback=self.button_release,  # method called here on button click
                on_release=True,  # tell button class to respond to release
            )
        except Exception as e:
            sys.print_exception(e)
            print("ENCODER NOT CREATED FOR ALARM DISABLE")
            raise

        # Initialize other components and state as needed
        self.update_display()

    def load_context(self):
        """
        Dequeue context from the queue and return the ui_context.
        """
        context = context_queue.dequeue()
        if context:
            print(
                f"alarm_disable,load_context,dequeue\n{context.router_context}\n{context.ui_context}\n{context_queue.size()}"
            )
        else:
            print("alarm_disable,load_context,dequeue: No context available")

        if isinstance(context, Context):
            return context.ui_context

        return context if context else {}

    def update_display(self):
        """
        Update the display on encoder changes
        """
        self.display.clear()
        self.display.update_text(self.header, 0, 0)
        # text_value = "Yes" if self.current_value else "No"
        text_value = "Yes"
        self.display.update_text(text_value, 0, 1)

    def poll_selection_change_and_update_display(self):
        """
        Detect if the encoder input has changed
        """
        pass

    def button_release(self):
        self.disable_alarm()
        self.build_context()
        return self.ui_context

    def build_context(self):
        next_ui_id = "main_menu"

        ui_context = {
            "header": "Main Menu",
            "selectables": [
                {"display_text": "Time", "id": "time_menu"},
                {"display_text": "Radio", "id": "radio_menu"},
            ],
        }
        router_context = {"next_ui_id": next_ui_id}
        context_queue.add_to_queue(
            Context(router_context=router_context, ui_context=ui_context)
        )

    def is_encoder_button_pressed(self):
        if self.encoder.get_button_state():
            return True
        return False

    def reset(self):
        self.current_value = 1  # self.min
        self.update_display()

    def stop(self):
        if self.encoder:
            self.encoder.pin_a.irq(handler=None)
            self.encoder.pin_b.irq(handler=None)
            self.encoder.button.disable_irq()
        if self.display:
            self.display.clear()

    def disable_alarm(self):
        """
        Disable the alarm in the RTC module.
        """
        self.rtc.alarm_off()
        self.encoder.reset_counter()
