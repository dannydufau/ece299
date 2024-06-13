from machine import Pin, Timer
from button import ButtonHandler
from display import CR_SPI_Display
import time
import _thread

SCREEN_WIDTH = 128
SCREEN_HEIGHT = 64

# SPI Device ID can be 0 or 1. It must match the wiring. 
SPI_DEVICE = 0

button_handler = ButtonHandler(button_pin=0, led_pin=15)

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

# Variable to store the last counter value
last_counter_value = button_handler.get_counter()

# Function to run in a separate thread
def check_counter():
    global last_counter_value
    while True:
        current_counter_value = button_handler.get_counter()
        if current_counter_value != last_counter_value:
            print(f"Counter changed: {current_counter_value}")
            last_counter_value = current_counter_value
            
        # Add a small delay to avoid a busy loop
        time.sleep(0.1)

# Start the counter checking in a new thread
_thread.start_new_thread(check_counter, ())


# Call the update_text method
display.update_text("ECE 299", 0, 0)
#display.update_text("Row 1", 0, 1)
#display.update_text("Row 100?", 0, 100)

# Main loop can be empty or perform other tasks
while True:
    pass

