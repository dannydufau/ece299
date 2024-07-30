# Create a new file frequency_config.py similar to volume_config.py

from ui import UI
from encoder import RotaryEncoder
from context_queue import context_queue
from context import Context


class FrequencyConfig(UI):
    def __init__(self, display, radio_control, encoder_pins, led_pin, id):
        self.display = display
        self.radio_control = radio_control
        self.id = id

        self.current_frequency = self.radio_control.get_frequency()  # Get current frequency
        
        # Load context
        self.ui_context = self.load_context()
        self.header = self.ui_context.get("header")
        self.min = self.ui_context.get("min", 88)
        #self.max = self.ui_context.get("max", 108)  # Range for FM frequency
        # Adjust range based on header
        self.max = self.ui_context.get("max", 9 if self.header == "fractional_part" else 108)
        self.current_value = self.min

        self.selected_index = None
        self.selected_item = None

        print(f"IN FREQUENCY CONFIG: {self.header}")

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
            print("ENCODER NOT CREATED FOR FREQUENCY CONFIG")
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

    def build_context(self, header, next_ui_id, min_value, max_value):
        ui_context = {
            "header": header,
            "min": min_value,
            "max": max_value
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
