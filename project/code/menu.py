from machine import Pin, Timer
from display import CR_SPI_Display
from encoder import RotaryEncoder
from ui import UI
import copy
import time
import sys
from context_queue import context_queue
from context import Context


class Menu(UI):
    def __init__(
        self,
        display,
        encoder_pins,
        led_pin,
        id,
        cursor=">",
    ):
        self.display = display
        self.id = id
        self.cursor_icon = cursor
        
        # Load context
        self.ui_context = self.load_context()
        self.header = self.ui_context.get("header")
        self.selectables = self.ui_context.get("selectables")
        self.selectables_count = len(self.selectables) if self.selectables else 0

        self.selected_index = None
        self.selected_item = None

        print(f"IN MENU: {self.header}")

        try:
            self.encoder = RotaryEncoder(
                pin_a=encoder_pins[0], 
                pin_b=encoder_pins[1], 
                pin_switch=encoder_pins[2], 
                led_pin=led_pin, 
                rollover=True,
                max=self.selectables_count,
                min=1
            )
        except Exception as e:
            sys.print_exception(e)
            print("ENCODER NOT CREATED FOR MENU")
            raise

        # Display header on row 0
        self.display.update_text(self.header, 0, 0)

        self.last_count = self._get_cursor_position_modulus()
        self._update_count_and_display(self.last_count)
        
    def _get_cursor_position_modulus(self):
        current_count = self.encoder.get_counter()[0]
        return current_count

    def _has_selection_changed(self):
        count = self.last_count
        if self._get_cursor_position_modulus() != self.last_count:
            return True
        return False
    
    def _update_cursor_to_current_selection(self, current_count):
        # Store the original texts
        original_texts = []
        for selectable in self.selectables:
            original_texts.append(selectable["display_text"])
            
        # Update the selected item's display text with the cursor icon
        print(f"selectables: {self.selectables}")
        #if current_count >= 0:  # ignore header
        #    self.selectables[current_count]["display_text"] = f"{self.cursor_icon} {self.selectables[current_count]['display_text']}"    
    
        if current_count > 0:  # Adjusted to properly ignore the header
            index = current_count - 1
            self.selectables[index]["display_text"] = f"{self.cursor_icon} {self.selectables[index]['display_text']}"
                
    
        # Update the display
        self.display.update_text(self.header, 0, 0)
        col = 0
        for i, selectable in enumerate(self.selectables):
            self.display.update_text(selectable["display_text"], col, i + 1)
        
        # Restore the original texts
        for i, selectable in enumerate(self.selectables):
            selectable["display_text"] = original_texts[i]

    def _update_count_and_display(self, current_count):
        self.last_count = current_count
        self._update_cursor_to_current_selection(current_count)

    def poll_selection_change_and_update_display(self):
        current_count = self._get_cursor_position_modulus()
        if self._has_selection_changed():
            self._update_count_and_display(current_count)
            return True
        return False
    
    def is_encoder_button_pressed(self):
        if self.encoder.get_button_state():
            self.select_action()
            return True
        return False

    def load_context(self):
        """
        Dequeue context from the queue and return the ui_context.
        """
        context = context_queue.dequeue()
        print(f"menu.py,load_context,dequeue\n{context.router_context}\n{context.ui_context}\n{context_queue.size()}")

        if isinstance(context, Context):
            return context.ui_context

        return context if context else {}

    def build_context(self):
        """
        Build the context for the next UI.
        """
        context_cp = self.ui_context.copy()
        if "context" in self.selected_item:
            context_cp.update(self.selected_item["context"])

        next_ui_id = self.selected_item["id"]
        context = Context(router_context={"next_ui_id": next_ui_id}, ui_context=context_cp)
        context_queue.add_to_queue(context)
        print(f"menu.py,build_context,add\n{context.router_context}\n{context.ui_context}\n{context_queue.size()}")

        return context

    def select_action(self):
        """
        Perform duties associated with the selected item and build context.
        """
        #self.selected_index = self.encoder.get_counter()[0]
        self.selected_index = self.encoder.get_counter()[0] - 1  # Adjusted for zero-based index
        self.selected_item = self.selectables[self.selected_index]
        self.build_context()

    def stop(self):
        if self.encoder:
            self.encoder.pin_a.irq(handler=None)
            self.encoder.pin_b.irq(handler=None)
            self.encoder.button.disable_irq()
        if self.display:
            self.display.clear()
