from machine import Pin, Timer
import time


class Button:
    def __init__(self, button_pin, led_pin, callback, identity, debounce_time_ms=200):
        self.led = Pin(led_pin, Pin.OUT)
        self.button = Pin(button_pin, Pin.IN, Pin.PULL_UP)
        self.callback = callback
        self.identity = identity
        self.button.irq(trigger=Pin.IRQ_FALLING, handler=self.handle_interrupt)
        
        self.debounce_time_ms = debounce_time_ms
        self.last_press_time_ms = 0
        
        # Flag to indicate if the callback is being processed
        self.processing = False  
        # TODO: delete this!
        self.radio_pwr_status = False

    def handle_interrupt(self, pin):
        if self.processing:
            print("Already running!")
            # If already processing, ignore further interrupts
            return
        
        self.process = True
        current_time_ms = time.ticks_ms()
        if time.ticks_diff(current_time_ms, self.last_press_time_ms) > self.debounce_time_ms:
            self.last_press_time_ms = current_time_ms
            self.led.toggle()
            self.callback(self.identity)
        #self.processing = False
        
# Example usage
#button_handler = ButtonHandler(button_pin=0, led_pin=15)

# Main loop can be empty or perform other tasks
#while True:
#    pass