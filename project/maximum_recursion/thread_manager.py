import utime
from menu import Menu
from button import Button
from thread_manager import ThreadManager

SCREEN_WIDTH = 128
SCREEN_HEIGHT = 64
SPI_DEVICE = 0

# Initialize the thread manager
thread_manager = ThreadManager()


def get_list_from_range(low, high):
    return list(range(low, high))


# Initialize radio power button
def initialize_radio_power():
    def radio_power_button_callback(identity):
        # Callback function for button interrupts
        print(f"radio power button called with identity: {identity}")
        stop_monitoring()  # kill existing loop, menu, and thread
        config = start_volume_config()

    button = Button(
        button_pin=0,
        callback=radio_power_button_callback,
        led_pin=15,
        identity='radio_power'
    )
    return button

# Menu configuration
def start_volume_config():
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
        header="Set the Volume",
        selectables=["1", "2"]
    )

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

def monitor_encoder_and_menu(menu):
    while not thread_manager.is_stopped():
        # Monitor encoder position and update display
        menu.poll_selection_change_and_update_display()
        # Monitor for encoder button selection
        if menu.is_encoder_button_pressed():
            new_selection = menu.get_selection()
            print(f"Button pressed, counter value: {new_selection}")

            if new_selection == 0:
                menu = start_time_menu()
            elif new_selection == 1:
                menu = start_radio_menu()
        
        utime.sleep(0.1)  # Small delay to avoid busy loop

def start_monitoring(menu):
    def target():
        monitor_encoder_and_menu(menu)
    print("start monitoring")
    thread_manager.start_thread(target)

def stop_monitoring():
    thread_manager.stop_thread()
    thread_manager.wait_for_stop()
    print("done stop thread")
    if hasattr(menu, 'stop_menu'):
        menu.stop_menu()
    print("done stop menu")

def mute():
    pass

radio_pwr_button = initialize_radio_power()
menu = start_main_menu()
start_monitoring(menu)

try:
    while True:
        if radio_pwr_button.button.value() == 0:
            radio_pwr_button.handle_interrupt(radio_pwr_button.button)
        utime.sleep(0.1)  # Main loop delay
except KeyboardInterrupt:
    stop_monitoring()
    print("Stopped monitoring")
