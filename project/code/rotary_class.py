from machine import Pin, Timer
import utime

# TODO(dd): integrate the LED for user feedback.

class RotaryEncoder:
    """
    Description: General purpose API for an encoder switch. Detect, debounce and report
    encoder dial and button events.  Debouncing strategy for the encoder is fairly involved.
    We detect both edge transitions (together representing a reliable change event) and
    decode the quadrature in a predetermined resolve window.  Incomplete quadratures are
    discarded as noise after timeout.  If a quadrature is discovered, we report the
    decoded direction and incr/decr the dial counter.
    In our testing, less than a full quadrature (edge transition) could be triggered
    with subtle dial movements, making an overly sensitive encoder.  
    """
    
    def __init__(
        self,
        pin_a,
        pin_b,
        pin_switch,
        led_pin,
        rollover=True,
        max=10,
        min=1,
        qtimeout_ms=150
    ):
        """
        Args:
            qtimeout_ms (ms): Specifies the time limit to which a full quadrature should be
                resolved.
            transition_count (int): tracks the four transition states of the encoder. If
                all four states are detected before the timeout we know we've completed a
                single unit of rotation and should report the counter and direction.
            last_transistion_time (ms): tracks when the last encoder state was last reported.
                We assume noise and should reset transition_count to zero if we don't
                complete a quadrature within a reasonable amount of time (qtimeout_ms).
            rollover (bool): If true the dial will rollover back to zero if max limit is
                reached rather than counting indefinitely.
        """
        self.pin_a = Pin(pin_a, mode=Pin.IN)
        self.pin_b = Pin(pin_b, mode=Pin.IN)
        self.pin_switch = Pin(pin_switch, mode=Pin.IN, pull=Pin.PULL_UP)
        self.led_pin = Pin(led_pin, mode=Pin.OUT, value=0)

        self.rollover = rollover
        self.max = max
        self.min = min
        self.counter = 0
        self.direction = ""
        self.state = (self.pin_a.value() * 2) + self.pin_b.value()
        self.last_state = self.state
        self.transition_count = 0
        self.last_transition_time = utime.ticks_ms()
        self.qtimeout_ms = qtimeout_ms
        self.button_last_state = False

        self.encoder_triggered = False
        self.button_triggered = False

        self.encoder_timer = Timer(-1)  # Timer for encoder debounce
        self.button_timer = Timer(-1)  # Timer for button debounce
        self.debounce_delay_ms = 2
        self.button_delay_ms = 10

        self.pin_a.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.encoder_irq)
        self.pin_b.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.encoder_irq)
        self.pin_switch.irq(trigger=Pin.IRQ_FALLING, handler=self.button_irq)

    def get_counter(self):
        return (self.counter, self.direction)
    
    def encoder_irq(self, pin):
        """
        Description: Debounce the encoder signal by catching the first detected edge and muting
        consecutive signals (contact noise) within the encoder_timer interval by setting
        encoder_triggered to True.  Call the actual handler after the timer interval.  We should reset the
        encoder_triggered to False after the real handler has completed!
        """
        if not self.encoder_triggered:
            self.encoder_triggered = True
            self.encoder_timer.init(mode=Timer.ONE_SHOT, period=self.debounce_delay_ms, callback=self.process_encoder)

    def button_irq(self, pin):
        """
        Description: Debounce the button signal described above.
        """
        if not self.button_triggered:
            self.button_triggered = True
            self.button_timer.init(mode=Timer.ONE_SHOT, period=self.button_delay_ms, callback=self.process_button)

    def update_counter(self, increment):
        if increment:
            self.counter += 1
            self.direction = "Clockwise"
            if self.counter > self.max:
                if self.rollover:
                    self.counter = self.min
                else:
                    self.counter = self.max
        else:
            self.counter -= 1
            self.direction = "Counter Clockwise"
            if self.counter < self.min:
                if self.rollover:
                    self.counter = self.max
                else:
                    self.counter = self.min

    def process_encoder(self, timer):
        """
        Description: Handle to debounced interrupt signal.
        1. Check if we have expired our time trying to resolve a quadrature.
            if we have expired, it is likely in a noisy state, reset it.
        2. Each interrupt compares the current state of the encoder
            with the previous state.  If a difference occurs we increment
            transition_count.
        3. When we've counted 4 states, we need to determine if state changed and
           in which direction.
           (self.pin_a.value() * 2) + self.pin_b.value() combines the pin values
           into a single integer (below). Note: multiplying by 2
           allows us to represent state 2,3 from 0,1.
            combines the pin values into a single integer:
                00: Both channels A and B are low.
                01: pin A is low, and pin B is high.
                10: pin A is high, and pin B is low.
                11: A and B are high.
        4. Directional patterns:
            Clockwise (CW) Rotation:

                Sequence: 00 -> 01 -> 11 -> 10 -> 00
                Corresponding decimal states: 0 -> 1 -> 3 -> 2 -> 0

            Counterclockwise (CCW) Rotation:

                Sequence: 00 -> 10 -> 11 -> 01 -> 00
                Corresponding decimal states: 0 -> 2 -> 3 -> 1 -> 0
        """
        state = (self.pin_a.value() * 2) + self.pin_b.value()
        current_time = utime.ticks_ms()

        # Check if too much time has passed since the last transition
        if utime.ticks_diff(current_time, self.last_transition_time) > self.qtimeout_ms:
            self.transition_count = 0  # Reset the transition count due to timeout

        # Detect state change
        if state != self.last_state:
            self.transition_count += 1
            self.last_transition_time = current_time  # Update the last transition time

            # Check for a complete cycle
            if self.transition_count == 4:
                self.transition_count = 0
                # Determine direction and update counter
                # Clockwise transitions
                if ((self.last_state == 0 and state == 1) or
                    (self.last_state == 1 and state == 3) or
                    (self.last_state == 3 and state == 2) or
                    (self.last_state == 2 and state == 0)):
                    self.update_counter(True)
                # Counterclockwise transitions
                elif ((self.last_state == 0 and state == 2) or
                      (self.last_state == 2 and state == 3) or
                      (self.last_state == 3 and state == 1) or
                      (self.last_state == 1 and state == 0)):
                    self.update_counter(False)

                print("Counter: ", self.counter, " | Direction: ", self.direction)
                print("\n")

            self.last_state = state

        self.encoder_triggered = False

    def process_button(self, timer):
        button_current_state = self.pin_switch.value() == 0  # ACTIVE LOW
        if button_current_state != self.button_last_state:
            if button_current_state:  # Button pressed
                print(f"Button is Pressed at counter: {self.counter}\n")
            self.button_last_state = button_current_state
        self.button_triggered = False

    def toggle_led(self):
        self.led_pin.toggle()

# Usage example:
if __name__ == "__main__":
    # Create an instance of the RotaryEncoder class
    encoder = RotaryEncoder(pin_a=19, pin_b=18, pin_switch=20, led_pin=25)


    # Main loop
    while True:
        encoder.toggle_led()
        utime.sleep(1)
