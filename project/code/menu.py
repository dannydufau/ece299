from machine import Pin, Timer
from display import CR_SPI_Display
from rotary_class import RotaryEncoder
import time
import _thread
import utime

class Event:
    def __init__(self):
        self._lock = _thread.allocate_lock()
        self._lock.acquire()

    def set(self):
        if not self._lock.locked():
            self._lock.acquire()

    def clear(self):
        if self._lock.locked():
            self._lock.release()

    def is_set(self):
        return self._lock.locked()

class Menu:
    def __init__(
        self,
        screen_width,
        screen_height,
        spi_device,
        spi_sck,
        spi_sda,
        spi_cs,
        res,
        dc,
        encoder_pins,
        led_pin,
        display_text
    ):
        # Initialize clock radio display for SPI
        self.display = CR_SPI_Display(
            screen_width=screen_width,
            screen_height=screen_height,
            spi_dev=spi_device,
            spi_sck=spi_sck,
            spi_sda=spi_sda,
            spi_cs=spi_cs,
            res=res,
            dc=dc
        )

        self.display_text = display_text

        # Initialize the display with static text
        # TODO: update for the number of lines in display text
        self.display.update_text(self.display_text[0], 2, 1)
        self.display.update_text(self.display_text[1], 2, 2)

        # Create an instance of the RotaryEncoder class
        self.encoder = RotaryEncoder(
            pin_a=encoder_pins[0], 
            pin_b=encoder_pins[1], 
            pin_switch=encoder_pins[2], 
            led_pin=led_pin, 
            rollover=True, 
            max=2
        )

        self.last_count = self.encoder.get_counter()[0]
        self.monitor_thread_running = False
        self.stop_event = Event()
        self.last_button_state = self.encoder.button_last_state
        self.button_state = self.encoder.button_last_state

    def check_counter_and_button(self):
        while not self.stop_event.is_set():
            current_count = self.encoder.get_counter()[0]

            if current_count != self.last_count:
                print(f"Counter changed: {current_count}")
                self.last_count = current_count
                
                # Update cursor position based on the counter value
                if current_count == 1:
                    self.display.update_text(f">{self.display_text[0]}", 0, 1)
                    self.display.update_text(f" {self.display_text[1]}", 0, 2)
                elif current_count == 2:
                    self.display.update_text(f">{self.display_text[1]}", 0, 2)
                    self.display.update_text(f" {self.display_text[0]}", 0, 1)
            
            # Check for button press
            button_state = self.encoder.button_last_state
            if button_state != self.last_button_state:
                self.button_state = button_state  # Update the button state in the class
                if button_state:
                    if current_count == 1:
                        self.display.update_text(f"{self.display_text[0]} Selected", 2, 3)
                    elif current_count == 2:
                        self.display.update_text(f"{self.display_text[1]} Selected", 2, 3)
                self.last_button_state = button_state

            # Add a small delay to avoid a busy loop
            time.sleep(0.1)
        print("Thread exiting gracefully")

    def get_button_state(self):
        return self.button_state
    
    def start_monitoring(self):
        if not self.monitor_thread_running:
            self.monitor_thread_running = True
            self.stop_event.clear()
            _thread.start_new_thread(self.check_counter_and_button, ())

    def stop_monitoring(self):
        self.stop_event.set()
        self.monitor_thread_running = False
        time.sleep(0.2)  # Allow time for the thread to exit
        self.disable_interrupts()

    def disable_interrupts(self):
        # Disable the interrupts for the encoder pins
        self.encoder.pin_a.irq(handler=None)
        self.encoder.pin_b.irq(handler=None)
        self.encoder.pin_switch.irq(handler=None)
