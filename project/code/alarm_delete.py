from machine import Pin, Timer
from display import CR_SPI_Display
from encoder import RotaryEncoder
import time
import sys
import uos
from ui import UI
from context_queue import context_queue
from context import Context


class AlarmDelete(UI):
    def __init__(
        self,
        display,
        rtc,
        encoder_pins,
        led_pin,
        alarm_id,
        header="Delete Alarm",
        min=0,
        max=1,
        next_config={"id": "main_menu", "display_text": "Main Menu"}
    ):
        self.display = display
        self.rtc = rtc
        self.alarm_id = alarm_id
        self.current_value = 0

        # Load context and populate properties
        self.ui_context = self.load_context()
        self.header = self.ui_context.get("header", "Delete Alarm?")
        self.min = self.ui_context.get("min", 0)
        self.max = self.ui_context.get("max", 1)
        self.current_value = self.min

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
        print("IN DELETE")

    def load_context(self):
        """
        Dequeue context from the queue and return the ui_context.
        """
        context = context_queue.dequeue()
        if context:
            print(f"alarm_delete,load_context,dequeue\n{context.router_context}\n{context.ui_context}\n{context_queue.size()}")
        else:
            print("alarm_delete,load_context,dequeue: No context available")

        if isinstance(context, Context):
            return context.ui_context

    def update_display(self):
        """
        Update the display on encoder changes
        """
        self.display.clear()
        self.display.update_text(self.header, 0, 0)
        text_value = "Yes" if self.current_value else "No"
        self.display.update_text(text_value, 0, 1)

    def poll_selection_change_and_update_display(self):
        """
        Detect if the encoder input has changed
        """
        new_value, direction = self.encoder.get_counter()
        if new_value != self.current_value:
            self.current_value = new_value
            self.update_display()

    def build_context(self):
        next_ui_id = "main_menu"
        
        ui_context = {
            "header": "Main Menu",
            "selectables": [
                {"display_text": "Time", "id": "time_menu"},
                {"display_text": "Radio", "id": "radio_menu"}
            ]
        }
        router_context = {"next_ui_id": next_ui_id}
        context_queue.add_to_queue(Context(router_context=router_context, ui_context=ui_context))
                    
    def select_action(self):
        if self.current_value == 0:
            print("should next config should be main")
        else:
            self.delete_alarm()
        self.build_context()
        
        # Do we need these next two lines?
        self.encoder.reset_counter()
        self.update_display()
        return self.ui_context

    def is_encoder_button_pressed(self):
        if self.encoder.get_button_state():
            self.select_action()
            return True
        return False

    def reset(self):
        self.current_value = 0
        self.update_display()

    def stop(self):
        self.encoder.pin_a.irq(handler=None)
        self.encoder.pin_b.irq(handler=None)
        self.encoder.button.disable_irq()

    def delete_alarm(self):
        """
        Delete the alarm in the RTC module.
        """
        self.rtc.delete_alarm(self.alarm_id)
        self.encoder.reset_counter()
