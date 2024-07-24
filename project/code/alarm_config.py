from context_queue import context_queue
from context import Context
from ui import UI
from encoder import RotaryEncoder
import sys


class AlarmConfig(UI):
    def __init__(self, display, rtc, encoder_pins, led_pin, min=None, max=None):
        # TODO: context values should also be optional args
        self.display = display
        self.rtc = rtc
        self.encoder_pins = encoder_pins
        self.led_pin = led_pin

        # Load context and populate properties
        self.ui_context = self.load_context()
        self.alarm_id = self.ui_context.get("alarm_id")
        
        # Default to "hour" if not provided
        self.header = self.ui_context.get("header", "hour")

        # Set from context
        self.min = self.ui_context.get("min", 0)
        self.max = self.ui_context.get("max", 24)
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
            print("ENCODER NOT CREATED FOR ALARM CONFIG")
            raise

        # Initialize other components and state as needed
        self.update_display()

    def load_context(self):
        """
        Dequeue context from the queue and return the ui_context.
        """
        context = context_queue.dequeue()
        print(f"alarm_config,load_context,dequeue\n{context.router_context}\n{context.ui_context}\n{context_queue.size()}")

        if isinstance(context, Context):
            return context.ui_context

        return context if context else {}

    def save_alarm_time(self):
        prefix="alarm_"
        existing_alarm_time = self.rtc.load_time(self.alarm_id, prefix) if self.alarm_id else None
        print(f"existing alarm: {existing_alarm_time}\n{self.alarm_id}")
        alarm_time = {
            'hour': existing_alarm_time['hour'] if existing_alarm_time else 0,
            'minute': existing_alarm_time['minute'] if existing_alarm_time else 0,
            'second': existing_alarm_time['second'] if existing_alarm_time else 0,
        }
        if self.header == "hour":
            alarm_time['hour'] = self.current_value
        elif self.header == "minute":
            alarm_time['minute'] = self.current_value
        elif self.header == "second":
            alarm_time['second'] = self.current_value
        
        if existing_alarm_time:
            self.rtc.save_alarm_time(self.alarm_id, alarm_time, prefix)
        else:
            self.alarm_id = self.rtc.new_alarm(alarm_time)
        
        print(f"Alarm time saved: {alarm_time}")

    def update_display(self):
        self.display.clear()
        #self.display.update_text(self.header.capitalize(), 0, 0)
        self.display.update_text(self.header, 0, 0)
        self.display.update_text(str(self.current_value), 0, 1)

    def poll_selection_change_and_update_display(self):
        new_value, direction = self.encoder.get_counter()
        if new_value != self.current_value:
            self.current_value = new_value
            self.update_display()

    def select_action(self):
        self.save_alarm_time()
        self.build_context()
        return self.ui_context

    def build_context(self):
        next_header = None
        next_ui_id = "set_alarm"
        min = None
        max = None
        if self.header == "hour":
            next_header = "minute"
            min = 0
            max = 59
        elif self.header == "minute":
            next_header = "second"
            min = 0
            max = 59
        elif self.header == "second":
            next_ui_id = "main_menu"
            next_header = ""
        
        ui_context = {
            "header": next_header,
            "min": min,
            "max": max,
            "alarm_id": self.alarm_id
        }
        router_context = {"next_ui_id": next_ui_id}
        context_queue.add_to_queue(Context(router_context=router_context, ui_context=ui_context))

    def is_encoder_button_pressed(self):
        if self.encoder.get_button_state():
            self.select_action()
            return True
        return False

    def reset(self):
        self.current_value = self.min
        self.update_display()

    def stop(self):
        if self.encoder:
            self.encoder.pin_a.irq(handler=None)
            self.encoder.pin_b.irq(handler=None)
            self.encoder.button.disable_irq()
        if self.display:
            self.display.clear()

    def turn_off_alarm(self):
        self.rtc.alarm_off()

    def disable_alarm(self):
        self.turn_off_alarm()
        snooze_time = self.rtc.get_snooze_time()
        if snooze_time:
            snooze_id = self.rtc.find_alarm_by_time(snooze_time)
            if snooze_id:
                self.rtc.delete_alarm(snooze_id, snooze=True)
        self.reporting_queue.add_to_queue({
            "job_id": "snooze_disable",
            "msg": None
        })
        self.encoder.reset_counter()
