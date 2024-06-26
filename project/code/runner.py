import utime
from menu import Menu
from button import Button

SCREEN_WIDTH = 128
SCREEN_HEIGHT = 64
SPI_DEVICE = 0


def start_time_config():
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
        header="Set the time",
        selectables=["Hours", "Minutes", "Seconds"]
    )


def start_alarm_config():
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
        header="Set the alarm",
        selectables=["Hours", "Minutes", "Seconds"]
    )


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
        header="Time Menu",
        selectables=["set time", "set alarm"]
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
        header="Radio Menu",
        selectables=["radio on", "radio off", "scan"]
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
        header="Main Menu",
        selectables=["time", "radio"]
    )

# TODO(dd): hold button key to reset

# TODO
#fm_radio = Radio(100.3, 2, False)


# Callback function for button interrupts
def button_callback(identity):
    #fm_radio.adjust_volume(identity)
    print(f"button_callback called with identity: {identity}")


#button_handler = ButtonHandler(button_pin=0, led_pin=15)
radio_pwr_button = Button(
    button_pin=0,
    callback=button_callback,
    led_pin=15,
    identity='radio_power'
)


menu = start_main_menu()
menu.start_monitoring()

try:
    while True:
        if menu.get_button_state():  # Check if the button is pressed
            counter_value = menu.get_cursor_position()
            print(f"Button pressed, counter value: {counter_value}")

            menu.stop_monitoring()  # Stop the current menu
            
            if counter_value == 0:
                menu = start_time_menu()
                menu.start_monitoring()
                
                while True:
                    if menu.get_button_state():
                        counter_value = menu.get_cursor_position()
                        print(f"time button pressed, counter value: {counter_value}")
                        menu.stop_monitoring()
                        if counter_value == 0:
                            print("Set the time!")
                            menu = start_time_config()
                            menu.start_monitoring()
                            
                        elif counter_value == 1:
                            print("Set the alarm!")
                            menu = start_alarm_config()
                            menu.start_monitoring()
                        else:
                            print("something unexpected")
                            
                    utime.sleep(0.1)

            elif counter_value == 1:
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