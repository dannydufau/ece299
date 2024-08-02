from ui import UI
from encoder import RotaryEncoder
from context_queue import context_queue
from context import Context

# import sys


class VolumeConfig(UI):
    def __init__(self, display, radio_control, encoder_pins, led_pin, id):
        self.display = display
        self.radio_control = radio_control
        self.id = id

        # Load context
        self.ui_context = self.load_context()
        self.header = self.ui_context.get("header")
        self.min = self.ui_context.get("min", 0)
        self.max = self.ui_context.get("max", 15)  # Default range for volume
        self.current_value = self.min

        self.selected_index = None
        self.selected_item = None

        print(f"IN VOLUME CONFIG: {self.header}")

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
            # sys.print_exception(e)
            print("ENCODER NOT CREATED FOR VOLUME CONFIG")
            raise

        self.update_display()

    def load_context(self):
        """
        Dequeue context from the queue and return the ui_context.
        """
        context = context_queue.dequeue()
        print(
            f"volume_config,load_context,dequeue\n{context.router_context}\n{context.ui_context}\n{context_queue.size()}"
        )

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
        self.radio_control.set_volume(self.current_value)
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

    def stop(self):
        if self.encoder:
            self.encoder.pin_a.irq(handler=None)
            self.encoder.pin_b.irq(handler=None)
            self.encoder.button.disable_irq()
        if self.display:
            self.display.clear()
