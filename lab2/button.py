from machine import Pin, Timer
import time

class ButtonHandler:
    def __init__(self, button_pin, led_pin, debounce_time_ms=200):
        self.led = Pin(led_pin, Pin.OUT)
        self.button = Pin(button_pin, Pin.IN, Pin.PULL_UP)
        self.debounce_time_ms = debounce_time_ms
        self.last_press_time_ms = 0
        self.counter = 0
        
        # Configure the interrupt
        self.button.irq(trigger=Pin.IRQ_FALLING, handler=self._button_handler)

    def _button_handler(self, pin):
        current_time_ms = time.ticks_ms()
        if time.ticks_diff(current_time_ms, self.last_press_time_ms) > self.debounce_time_ms:
            self.last_press_time_ms = current_time_ms
            self.led.toggle()
            self.counter += 1
            print(self.counter)
            
    def get_counter(self):
        return self.counter

# Example usage
#button_handler = ButtonHandler(button_pin=0, led_pin=15)

# Main loop can be empty or perform other tasks
#while True:
#    pass