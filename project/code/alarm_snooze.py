from context_queue import context_queue, reporting_queue
from context import Context
from ui import UI
from encoder import RotaryEncoder
import sys


class AlarmSnooze(UI):
    def __init__(
        self,
        display,
        rtc,
        encoder_pins,
        led_pin,
    ):
        self.display = display
        self.rtc = rtc
        
        # Load context and populate properties
        self.ui_context = self.load_context()

        self.header = self.ui_context.get("header", "Disable Snooze Alarm")
        self.min = self.ui_context.get("min", 0)
        self.max = self.ui_context.get("max", 1)
        self.snooze = self.ui_context.get("snooze", False)

        self.current_value = self.min
        
        # Initialize the encoder
        try:
            self.encoder = RotaryEncoder(
                pin_a=encoder_pins[0], 
                pin_b=encoder_pins[1], 
                pin_switch=encoder_pins[2], 
                led_pin=led_pin, 
                rollover=True,
                max=self.max,
                min=self.min
            )
        except Exception as e:
            sys.print_exception(e)
            print("ENCODER NOT CREATED FOR ALARM SNOOZE")
            raise

        self.update_display()

        # Initialize a snooze if required
        if self.snooze:
            self.trigger_snooze()

    def load_context(self):
        """
        Dequeue context from the queue and return the ui_context.
        """
        context = context_queue.dequeue()
        if context:
            print(f"alarm_snooze,load_context,dequeue\n{context.router_context}\n{context.ui_context}\n{context_queue.size()}")

        if isinstance(context, Context):
            return context.ui_context

        return context if context else {}

    def trigger_snooze(self):
        snooze_minutes = 1  # minutes to snooze

        # Turn off alarm sound activated by previous alarm triggering snooze
        self.turn_off_alarm()
        
        # Delete any existing snooze files
        self.rtc.delete_all_snooze_files()

        # Create a new snooze alarm file and get the snooze time
        snooze_id, snooze_time = self.rtc.new_snooze(snooze_minutes)
        #print(f"HSHSHSHS: {snooze_time}")
        msg = f"Snooze active until {snooze_time['hour']:02d}:{snooze_time['minute']:02d}:{snooze_time['second']:02d}"

        # Queue up message "snooze active" in reporting queue with the snooze trigger time
        reporting_queue.add_to_queue({
            "job_id": "snooze_active",
            "msg": msg,
            "snooze_time": snooze_time
        })

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

    def select_action(self):
        if self.current_value == 1:  # If "Yes" is selected
            self.disable_alarm()
        self.build_context()
        return self.ui_context

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
        
    def turn_off_alarm(self):
        self.rtc.alarm_off()
        
    def disable_alarm(self):
        """
        Disable the snooze alarm in the RTC module.
        """
        # Should already be turned off
        self.turn_off_alarm()
        
        # Remove any snooze files
        self.rtc.delete_all_snooze_files()
        
        # Enqueue "snooze inactive" message
        reporting_queue.add_to_queue({
            "job_id": "snooze_disable",
            "msg": None
        })
        self.encoder.reset_counter()
        
        # Set alarm_active to False
        self.rtc.alarm_active = False

