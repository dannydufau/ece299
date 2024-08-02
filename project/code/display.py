from ssd1306 import (
    SSD1306_SPI,
)  # this is the driver library and the corresponding class
import framebuf  # this is another library for the display.
from machine import Pin, SPI
import utime


SCREEN_WIDTH = 128
SCREEN_HEIGHT = 64

# SPI Device ID can be 0 or 1. It must match the wiring.
SPI_DEVICE = 0


class CR_SPI_Display:
    def __init__(
        self,
        spi_sck,
        spi_sda,  # sda is MOSI
        spi_cs,
        spi_dev,
        res,
        dc,
        screen_width=128,
        screen_height=64,
        baudrate=100000,
    ):
        """
        Args:
            screen_width (int): Define # of pixel columns of the oled display.
            screen_height (int): Define # of pixel rows of the oled display.
            spi_sck (int): serial clock; always be connected to SPI SCK pin of the Pico
            spi_sda, (int): MOSI pin masquerading as sda (i2c), always be connected to SPI TX pin of the Pico.
            res (int): reset; to be connected to a free GPIO pin.
            dc (int): data/command; to be connected to a free GPIO pin.
            spi_cs (int): chip select; to be connected to the SPI chip select of the Pico.
            spi_dev (int): spi device on Pico.
            baudrate (int): changes to signal per second.
        Returns:
        """
        self.baudrate = baudrate
        self.dev = spi_dev

        # Initialize I/O pins associated with the oled display SPI interface
        self.sck = Pin(spi_sck)
        self.sda = Pin(spi_sda)
        # NOTE: hooked up res to what would normally be rx gp4
        self.res = Pin(res)
        self.dc = Pin(dc)
        self.cs = Pin(spi_cs)

        # initialize the SPI interface for the OLED display
        oled_spi = SPI(self.dev, self.baudrate, sck=self.sck, mosi=self.sda)

        # Initialize the display
        self.oled = SSD1306_SPI(
            screen_width,
            screen_height,
            oled_spi,
            self.dc,
            self.res,
            self.cs,
            False,  # external_vcc=False
        )
        # self.enable()
        # Set display pixel to character multiplier
        # https://docs.micropython.org/en/latest/library/framebuf.html
        # see Framebuffer.text
        self.char_height_px = 8
        self.char_width_px = 8

        # Set maximum limits for columns and rows in terms of chars
        self.max_columns = self.oled.width // self.char_width_px
        self.max_rows = self.oled.height // self.char_height_px

        # print(f"max columns: {self.max_columns}")
        # print(f"max rows: {self.max_rows}")

    def clear(self):
        """
        Clear entire the buffer
        """
        self.oled.fill(0)
        self.oled.show()

    def _clear_row(self, row, update_display=True):
        """
        Description: convenience method to clear an area that
        is letter height.
        Args:
            row (int): specific row to clear
            update_display (bool): whether to update the display after clearing the row
        """
        y = row * self.char_height_px
        self.oled.fill_rect(0, y, self.oled.width, self.char_height_px, 0)
        # prevent multiple recursion error
        if update_display:
            self.oled.show()

    def _update_row(self, text, column, row, color=1, tab=True, update_display=True):
        """
        Render the text at the specified location
        Args:
            text (str):
            column (int):
            row (int):
            color (int): black 0, white 1
            tab (bool): adds space to accommodate cursor
            update_display (bool): whether to update the display after updating the row
        """
        x = column * self.char_width_px + 2
        y = row * self.char_height_px
        self.oled.text(text, x, y, color)
        if update_display:
            self.oled.show()

    def update_text(self, text, column, row, color=1):
        """
        Description:
        Letters are 8 (pixels) high, set rows to reflect sentence height.
        Check that row/column args to overrun configured display buffers.
        Framebuffer.text 8x8 pixel characters only.
        https://docs.micropython.org/en/latest/library/framebuf.html

        # NOTE: the current SSD1306 module and framebuf library we are
        # using do not support different fonts out of the box. Instead, we need to
        # manually implement a way to handle different fonts for different sizes.
        # May need https://docs.circuitpython.org/projects/display_text/en/latest/
        """

        # Ensure column and row are within limits
        if column < 0:
            column = 0
        elif column >= self.max_columns:
            # TODO: might want to raise warning if text exceeds limits
            column = self.max_columns - 1

        if row < 0:
            row = 0
        elif row >= self.max_rows:
            row = self.max_rows - 1

        # Clear the specified row without updating the display immediately
        self._clear_row(row, update_display=False)
        # Update the row without updating the display immediately
        self._update_row(text, column, row, color, update_display=False)

        # Update the display
        self.oled.show()

    def enable(self):
        self.oled.poweron()

    def release(self):
        self.clear()
        # self.oled.poweroff()
        # print("poweroff complete")


class CR_SPI_Display_Second(CR_SPI_Display):
    def __init__(
        self,
        screen_width=128,
        screen_height=64,
        spi_dev=1,
        spi_sck=10,
        spi_sda=11,
        spi_cs=13,
        res=14,
        dc=12,
        baudrate=100000,
    ):
        super().__init__(
            spi_sck,
            spi_sda,
            spi_cs,
            spi_dev,
            res,
            dc,
            screen_width,
            screen_height,
            baudrate,
        )


if __name__ == "__main__":

    # Initialize clock radio display for SPI
    display = CR_SPI_Display(
        screen_width=SCREEN_WIDTH,
        screen_height=SCREEN_HEIGHT,
        spi_dev=SPI_DEVICE,
        spi_sck=2,
        spi_sda=3,
        spi_cs=5,
        res=4,
        dc=6,
    )

    # Call the update_text method
    display.update_text("ECE 299", 0, 0, 3)

    display.oled.fill(0)
    display.oled.fill_rect(0, 0, 32, 32, 1)
    display.oled.fill_rect(2, 2, 28, 28, 0)
    display.oled.vline(9, 8, 22, 1)
    display.oled.vline(16, 2, 22, 1)
    display.oled.vline(23, 8, 22, 1)
    display.oled.fill_rect(26, 24, 2, 4, 1)
    display.oled.text("ECE 299", 40, 0, 1)
    display.oled.text("SSD1306", 40, 12, 1)
    display.oled.text("OLED 128x64", 40, 24, 1)
    display.oled.show()
