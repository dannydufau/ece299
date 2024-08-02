import uos
from machine import Pin
from display import CR_SPI_Display
from encoder import RotaryEncoder
from rtc import RealTimeClock
from ui import UI
import copy
import time
import sys
from context_queue import context_queue
from context import Context


class TimeZoneConfig(UI):
    CONFIG_FILE = "timezone_config.txt"
    TIMEZONES = ["UTC", "CST", "CDT", "PST"]

    def __init__(
        self,
        display,
        encoder_pins,
        led_pin,
        rtc,
        cursor=">",
    ):
        self.display = display
        self.cursor_icon = cursor
        self.rtc = rtc

        # Load context
        self.ui_context = self.load_context()
        self.header = self.ui_context.get("header")
        self.selectables = self.ui_context.get("selectables")
        self.selectables_count = len(self.selectables) if self.selectables else 0

        self.selected_index = None
        self.selected_item = None

        # print(f"timezone: {self.header}")
        # print(f"timezone: {self.selectables}")
        print(f"timezone: {self.selectables_count}")

        try:
            self.encoder = RotaryEncoder(
                pin_a=encoder_pins[0],
                pin_b=encoder_pins[1],
                pin_switch=encoder_pins[2],
                led_pin=led_pin,
                rollover=True,
                max=self.selectables_count,
                min=1,
                button_callback=self.button_release,  # method called here on button click
                on_release=True,  # tell button class to respond to release
            )
        except Exception as e:
            sys.print_exception(e)
            print("ENCODER NOT CREATED FOR MENU")
            raise

        # Display header on row 0
        self.display.clear()
        self.display.update_text(self.header, 0, 0)

        self.last_count = self._get_cursor_position_modulus()
        self._update_count_and_display(self.last_count)

    def load_context(self):
        """
        Dequeue context from the queue and return the ui_context.
        """
        context = context_queue.dequeue()
        print(
            f"menu.py,load_context,dequeue\n{context.router_context}\n{context.ui_context}\n{context_queue.size()}"
        )

        if isinstance(context, Context):
            return context.ui_context

        return context if context else {}

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
        # if current_count >= 0:  # ignore header
        #    self.selectables[current_count]["display_text"] = f"{self.cursor_icon} {self.selectables[current_count]['display_text']}"

        if current_count > 0:  # Adjusted to properly ignore the header
            index = current_count - 1
            self.selectables[index][
                "display_text"
            ] = f"{self.cursor_icon} {self.selectables[index]['display_text']}"

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
        # being replaced by button_release
        if self.encoder.get_button_state():
            return True
        return False

    def build_context(self):
        """
        Build the context for the next UI.
        """
        try:
            # After setting the time mode, return to the main menu
            context = Context(
                router_context={"next_ui_id": "main_menu"},
                ui_context={
                    "header": "Main Menu",
                    "selectables": [
                        {"display_text": "Time", "id": "time_menu"},
                        {"display_text": "Radio", "id": "radio_menu"},
                    ],
                },
            )
            context_queue.add_to_queue(context)
        except Exception as e:
            print(f"Error in timezone build context.\n{e}")

    def button_release(self):
        self.selected_index = self.encoder.get_counter()[0] - 1
        self.selected_item = self.selectables[self.selected_index]
        self.encoder.reset_counter()
        self.set_timezone()
        self.build_context()

    def set_timezone(self):
        current_zone = self.rtc.load_timezone()
        selected_zone = self.selected_item["id"]
        print(f"CURRENT ZONE: {current_zone}\nSelected zone: {selected_zone}")
        if selected_zone == current_zone:
            return
        try:
            current_time = self.rtc.rtc.datetime()
            new_time, _ = self.rtc.convert_timezone(current_time, selected_zone)
            print(f"current time: {current_time}, new_time: {new_time}")
            self.rtc.set_datetime(*new_time[:7])
            self.save_timezone(selected_zone)
            self.current_zone = selected_zone

        except Exception as e:
            print(f"Failed to set timezone. Error: {e}")

    def save_timezone(self, timezone):
        try:
            with open(self.CONFIG_FILE, "w") as file:
                file.write(timezone)
            print(f"Timezone {timezone} saved to {self.CONFIG_FILE}")
        except Exception as e:
            print(f"Failed to save timezone. Error: {e}")

    def file_exists(self, filepath):
        try:
            uos.stat(filepath)
            return True
        except OSError:
            return False

    def stop(self):
        self.encoder.pin_a.irq(handler=None)
        self.encoder.pin_b.irq(handler=None)
        self.encoder.button.disable_irq()
