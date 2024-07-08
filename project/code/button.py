from machine import Pin, Timer
import time
from led import LED


class Button:
    def __init__(self, button_pin, led_pin, callback, identity, debounce_time_ms=10):
        self.led = LED(led_pin)
        self.button = Pin(button_pin, Pin.IN, Pin.PULL_UP)
        self.callback = callback
        self.identity = identity
        self.button.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=self.button_irq)
        
        # Timer for button debounce
        self.button_timer = Timer(-1)
        self.button_triggered = False
        self.button_delay_ms = debounce_time_ms
        
        # Track last button state
        self.button_last_state = False

    def process_button(self, timer):
        button_current_state = self.button.value() == 0  # ACTIVE LOW
        #print(f"button triggered, current state: {button_current_state}, last state: {self.button_last_state}")
        
        if button_current_state != self.button_last_state:
            if button_current_state:  # Button pressed
                self.led.toggle()
                print(f"Button is Pressed: {self.identity}")
                self.callback(self.identity)
            else:  # Button released
                #print(f"Button is Released: {self.identity}")
                pass
            

        self.button_last_state = button_current_state
        self.button_triggered = False

    def button_irq(self, pin):
        """
        Description: Debounce the button signal described above.
        """
        if not self.button_triggered:
            self.button_triggered = True
            self.button_timer.init(
                mode=Timer.ONE_SHOT,
                period=self.button_delay_ms,
                callback=self.process_button
            )

    def disable_irq(self):
        """
        Allows dynamic disable of irq. e.g. loading a new menu with a fresh
        mapping to encoder button.  
        """
        self.button.irq(handler=None)