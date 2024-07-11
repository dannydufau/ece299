from machine import Pin, Timer
from display import CR_SPI_Display
from encoder import RotaryEncoder
import sys


class UI:
    def __init__(self, screen_width, screen_height, spi_device, spi_sck, spi_sda, spi_cs, res, dc, encoder_pins, led_pin, header):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.spi_device = spi_device
        self.spi_sck = spi_sck
        self.spi_sda = spi_sda
        self.spi_cs = spi_cs
        self.res = res
        self.dc = dc
        self.encoder_pins = encoder_pins
        self.led_pin = led_pin
        self.header = header
        self.display = None

    def poll_selection_change_and_update_display(self):
        raise NotImplementedError

    def get_selection(self):
        raise NotImplementedError

    def is_encoder_button_pressed(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError
