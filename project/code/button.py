from machine import Pin, Timer
import time
import utime
from led import LED


class Button:
    def __init__(
        self,
        button_pin,
        led_pin,
        callback,
        identity,
        debounce_time_ms=10,
        on_release=False,
        *args,
        **kwargs,
    ):
        # track if callback should be triggered on release
        self.on_release = on_release

        self.led = LED(led_pin)
        self.button = Pin(button_pin, Pin.IN, Pin.PULL_UP)
        self.callback = callback
        self.identity = identity
        self.button.irq(
            trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=self.button_irq
        )

        # Timer for button debounce
        self.button_timer = Timer(-1)
        self.button_triggered = False
        self.button_delay_ms = debounce_time_ms

        # Track last button state
        self.button_last_state = False

        # contains additional callback data e.g. queues
        self.args = args
        self.kwargs = kwargs

    def _callback_wrapper(self):
        """
        Description:  Call the passed in call back with necessary args
        """
        # print(f"Callback called for identity: {self.identity}")
        self.callback(self.identity, *self.args, **self.kwargs)

    def process_button(self, timer):
        button_current_state = self.button.value() == 0  # ACTIVE LOW
        # print(f"Button current state: {button_current_state}, Last state: {self.button_last_state}")

        if button_current_state != self.button_last_state:
            if (
                button_current_state and not self.on_release
            ):  # Button pressed and callback on press
                self.led.on_ms(100)
                self._callback_wrapper()  # Use the wrapper to call the callback with additional arguments
            elif (
                not button_current_state and self.on_release
            ):  # Button released and callback on release
                self._callback_wrapper()  # Use the wrapper to call the callback with additional arguments
                # print("button.py,process_button,button released")
        self.button_last_state = button_current_state
        self.button_triggered = False

    def process_buttonOriginal(self, timer):
        button_current_state = self.button.value() == 0  # ACTIVE LOW
        if button_current_state != self.button_last_state:
            if button_current_state:  # Button pressed
                self.led.on_ms(100)
                self._callback_wrapper()  # Use the wrapper to call the callback with additional arguments
            else:  # Button released
                print("button.py,process_button,button released")
                # pass
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
                callback=self.process_button,
            )

    def disable_irq(self):
        """
        Allows dynamic disable of irq. e.g. loading a new menu with a fresh
        mapping to encoder button.
        """
        self.button.irq(handler=None)


if __name__ == "__main__":

    def radio_button_callback(identity, auxiliary_queue):
        print(f"Button {identity} pressed")

    print("test")
    radio_pwr_button = Button(
        button_pin=9,  # 0 bb, 15 on pcb
        led_pin=8,  # 15 on bb, 8 on pcb
        callback=radio_button_callback,
        identity="radio_power",
        debounce_time_ms=10,
        auxiliary_queue=None,
    )
    while True:
        print("test")
        utime.sleep(1)
