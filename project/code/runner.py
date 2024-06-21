import utime
from menu import Menu

SCREEN_WIDTH = 128
SCREEN_HEIGHT = 64
SPI_DEVICE = 0

def start_time_menu():
    return Menu(
        screen_width=SCREEN_WIDTH,
        screen_height=SCREEN_HEIGHT,
        spi_device=SPI_DEVICE,
        spi_sck=2,
        spi_sda=3,
        spi_cs=5,
        res=4,
        dc=6,
        encoder_pins=(19, 18, 20),
        led_pin=25,
        display_text=("set time", "set alarm")
    )    

def start_radio_menu():
    return Menu(
        screen_width=SCREEN_WIDTH,
        screen_height=SCREEN_HEIGHT,
        spi_device=SPI_DEVICE,
        spi_sck=2,
        spi_sda=3,
        spi_cs=5,
        res=4,
        dc=6,
        encoder_pins=(19, 18, 20),
        led_pin=25,
        display_text=("radio on", "radio off", "scan")
    )

def start_main_menu():
    return Menu(
        screen_width=SCREEN_WIDTH,
        screen_height=SCREEN_HEIGHT,
        spi_device=SPI_DEVICE,
        spi_sck=2,
        spi_sda=3,
        spi_cs=5,
        res=4,
        dc=6,
        encoder_pins=(19, 18, 20),
        led_pin=25,
        display_text=("time", "radio")
    )

# TODO(dd): hold button key to reset

menu = start_main_menu()
menu.start_monitoring()

try:
    while True:
        if menu.get_button_state():  # Check if the button is pressed
            counter_value = menu.encoder.get_counter()[0]
            print(f"Button pressed, counter value: {counter_value}")
            print("Restarting menu...")
            menu.stop_monitoring()  # Stop the current menu
            
            if counter_value == 1:
                menu = start_time_menu()
                menu.start_monitoring()
                while True:
                    if menu.get_button_state():
                        print("time button pressed!")
                    utime.sleep(0.1)
                    
                
            elif counter_value == 2:
                menu = start_radio_menu()
                menu.start_monitoring()
                while True:
                    if menu.get_button_state():
                        print("radio button pressed!")
                    utime.sleep(0.1)
            
        utime.sleep(0.1)  # Small delay to avoid busy loop
except KeyboardInterrupt:
    menu.stop_monitoring()
    print("Stopped monitoring")

