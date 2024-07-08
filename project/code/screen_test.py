from machine import Pin, SPI
from ssd1306 import SSD1306_SPI
import utime

# Define the pins
spi_sck = 10
spi_mosi = 11
spi_cs = 12
res = 13
dc = 14

# Initialize the SPI interface
spi = SPI(1, baudrate=100000, polarity=0, phase=0, sck=Pin(spi_sck), mosi=Pin(spi_mosi))

# Initialize the display
oled = SSD1306_SPI(128, 64, spi, Pin(dc), Pin(res), Pin(spi_cs))

# Clear the display
oled.fill(0)
oled.show()

# Display test message
oled.text('Hello, World!', 0, 0)
oled.show()

while True:
    print("h")
    utime.sleep(1)
