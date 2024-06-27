from ssd1306 import SSD1306_SPI  # this is the driver library and the corresponding class
import framebuf  # this is another library for the display. 
from machine import Pin, SPI

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
        oled_spi = SPI(
            self.dev,
            self.baudrate,
            sck=self.sck,
            mosi=self.sda
        )

        # Initialize the display
        self.oled = SSD1306_SPI(
            screen_width,
            screen_height,
            oled_spi,
            self.dc,
            self.res,
            self.cs,
            True
        )

        # Set display pixel to character multiplier
        self.char_height_px = 10
        self.char_width_px = 6

        # Set maximum limits for columns and rows in terms of chars
        self.max_columns = self.oled.width // self.char_width_px
        self.max_rows = self.oled.height // self.char_height_px
        
        print(f"max columns: {self.max_columns}")
        print(f"max rows: {self.max_rows}")

    def clear(self):
        """
        Clear entire the buffer
        """
        self.oled.fill(0)
        self.oled.show()

    def _clear_row(self, row):
        """
        Description: convenience method to clear an area that
        is letter height.
        Args:
            row (int): specific row to clear
        """
        y = row * self.char_height_px
        self.oled.fill_rect(0, y, self.oled.width, 10, 0)
        
    def _update_row(self, text, column, row):
        """
        Render the text at the specified location
        Args:
            text (str):
            column (int):
            row (int):
        """
        x = column * self.char_width_px
        y = row * self.char_height_px
        self.oled.text(text, x, y)
        
    def update_text(self, text, column, row):
        """
        Description:
        Letters are 10 (pixels) high, set rows to reflect sentence height.
        Check that row/column args to overrun configured display buffers.
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
        
        # Clear the specified row
        self._clear_row(row)

        self._update_row(text, column, row)

        # Update the display
        self.oled.show()

# Usage example:
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
        dc=6
    )

    # Call the update_text method
    display.update_text("ECE 299", 0, 0)

