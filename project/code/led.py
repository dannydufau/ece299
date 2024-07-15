import machine
import utime


class LED:
    def __init__(self, pin):
        self.led = machine.Pin(pin, machine.Pin.OUT)
    
    def on(self):
        self.led.value(1)
    
    def off(self):
        self.led.value(0)
    
    def blink(self, duration=0.5, times=3):
        for _ in range(times):
            self.on()
            utime.sleep(duration)
            self.off()
            utime.sleep(duration)

if __name__ == "__main__":
    led = LED(25)  # GPIO25
    led.blink()
