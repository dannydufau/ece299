from machine import Pin, Timer


class LED:
    def __init__(self, pin_number):
        self.led = Pin(pin_number, Pin.OUT)
        self.state = False
        self.timer = Timer(-1)  # Timer for handling LED off delay

    def on(self):
        self.led.value(1)
        self.state = True

    def off(self):
        self.led.value(0)
        self.state = False

    def on_ms(self, duration_ms=None):
        self.state = not self.state
        self.led.value(self.state)
        if duration_ms:
            self.timer.init(
                mode=Timer.ONE_SHOT, period=duration_ms, callback=lambda t: self.off()
            )

    def is_on(self):
        return self.state
