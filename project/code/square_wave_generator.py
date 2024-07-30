from machine import Pin, PWM
import time


class SquareWaveGenerator:
    def __init__(self, pin, frequency):
        self.pin = Pin(pin)
        self.pwm = PWM(self.pin)
        self.set_frequency(frequency)
    
    def set_frequency(self, frequency):
        self.pwm.freq(frequency)
        self.pwm.duty_u16(32768)  # 50% duty cycle (0-65535 range)
    
    def start(self):
        self.pwm.init(freq=self.pwm.freq(), duty_u16=32768)
    
    def stop(self):
        self.pwm.deinit()

# Example usage:
if __name__ == "__main__":
    square_wave = SquareWaveGenerator(22, 888)  # GP22, 1 kHz frequency
    square_wave.start()
    
    try:
        while True:
            time.sleep(1)  # Keep running
    except KeyboardInterrupt:
        square_wave.stop()
        print("Square wave generation stopped.")
