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
        header,
        selectables,
        cursor=">"
    ):
        self.header = header
        self.selectables = selectables
        self.selectables_count = len(selectables)
        self.cursor_icon = cursor

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

        # Create an instance of the RotaryEncoder class
        self.encoder = RotaryEncoder(
            pin_a=encoder_pins[0], 
            pin_b=encoder_pins[1], 
            pin_switch=encoder_pins[2], 
            led_pin=led_pin, 
            rollover=True, 
            max=self.selectables_count # modulus rollover 
        )
        
        self.set_display()
        self.last_count = self.get_cursor_position()
        self.monitor_thread_running = False
        self.stop_event = Event()
        self.last_button_state = self.get_button_state()
        self.button_state = self.get_button_state()

    def get_button_state(self):
        #print(f"encoder button pressed {self.encoder.button_last_state}")
        return self.encoder.button_last_state

    def get_cursor_position(self):
        current_count = self.encoder.get_counter()[0]
        current_count -= 1
        if (current_count < 0):
            current_count = 0
        return current_count

    def set_display(self):
        """
        Description: Initializes display from and array of text strings.
            Header is first row.
            Remaining rows are selectable items.
            cursor assigned to selectable item associated with counter.
        """

        # set the cursor at the encoder position
        current = self.get_cursor_position()
        print(f"counter position: {current}")
        
        # Get a copy of selectables for cursor mutation
        selectables = list(self.selectables)

        original_text = selectables[current]
        selectables[current] = f"{self.cursor_icon} {original_text}"
        
        # update display
        col = 0
        
        # Update display for the number of selectable items present
        for i in range(len(selectables)):
            self.display.update_text(selectables[i], col, i + 2)
        
    def track_encoder(self):
        """
        Description: Tracks for encoder rotations
        """

        while not self.stop_event.is_set():
            current_count = self.get_cursor_position()

            if current_count != self.last_count:
                print(f"Counter changed: {current_count}")
                self.last_count = current_count
                
                self.set_display()
                
            #print(f"button state: {self.get_button_state()}\nlast state: {self.last_button_state}")
                
            # Add a small delay to avoid a busy loop
            time.sleep(0.1)
        print("Thread exiting gracefully")
    
    def start_monitoring(self):
        if not self.monitor_thread_running:
            self.monitor_thread_running = True
            self.stop_event.clear()
            _thread.start_new_thread(self.track_encoder, ())

    def stop_monitoring(self):
        self.stop_event.set()
        self.monitor_thread_running = False
        time.sleep(0.2)  # Allow time for the thread to exit
        self.disable_interrupts()

    def disable_interrupts(self):
        print("disable interrupts called")
        # Disable the interrupts for the encoder pins
        self.encoder.pin_a.irq(handler=None)
        self.encoder.pin_b.irq(handler=None)
        self.encoder.pin_switch.irq(handler=None)
