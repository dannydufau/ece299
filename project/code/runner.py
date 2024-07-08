import utime
from menu import Menu
from button import Button
from thread_manager import ThreadManager
from queue_handler import queue_handler

from display import CR_SPI_Display, CR_SPI_Display_Second

SCREEN_WIDTH = 128
SCREEN_HEIGHT = 64
SPI_DEVICE = 0

SCREEN2_WIDTH = 128#96  # New width
SCREEN2_HEIGHT = 64#16  # New height
SPI_DEVICE2 = 1

# Initialize the thread manager
thread_manager = ThreadManager()


def get_list_from_range(low, high):
    return [str(i) for i in range(low, high)]


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
        led_pin=15,
        header="Set the Volume",
        selectables=get_list_from_range(1, 5),
        id="set_volume"
        # TODO: we want 1 selectable and as the knob turns the 1 selectable incr/decr
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
        led_pin=15,
        header="Set the time",
        selectables=["Hours", "Minutes", "Seconds"],
        id="set_time"
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
        led_pin=15,
        header="Set the alarm",
        selectables=["Hours", "Minutes", "Seconds"],
        id="set_alarm"
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
        led_pin=15,
        header="Time Menu",
        selectables=[
            {"display_text": "set time", "id": "set_time"},
            {"display_text": "set alarm", "id": "set_alarm"}
        ],
        id="time_menu"
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
        led_pin=15,
        header="Radio Menu",
        selectables=[
            {"display_text": "radio on", "id": "some_radio_config"},
            {"display_text": "Radio Off", "id": "some_radio_config"},
            {"display_text": "Frequency scan", "id": "scan"}
        ],
        id="radio_menu"
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
        led_pin=15,
        header="Main Menu",
        selectables=[
            {"display_text": "Time", "id": "time_menu"},
            {"display_text": "Radio", "id": "radio_menu"}],
        id="main_menu"
    )


menu_map = {
    "set_volume": start_volume_config,
    "set_time": start_time_config,
    "set_alarm": start_alarm_config,
    "time_menu": start_time_menu,
    "radio_menu": start_radio_menu,
    "main_menu": start_main_menu
}


def get_menu_from_button(id):
    """
    Description: This is called on aux button interrupt only
    Note: id can be a button id or a menu_id or a stop command
    """

    if id == "radio_power":
        # the radio_power button was hit
        menu = start_volume_config()

    elif id == "start_main_menu":
        menu = start_main_menu()
        
    # TODO: need custom handling here..
    elif id == "stop_monitoring":
        thread_manager.stop_thread()
        menu.stop_menu()
        return
    
    #print(f"id: {id}")
    return menu


def load_menu(current_menu, new_menu_item):
    """
    Description: Stop the current menu gracefully, load the new menu.
    """
    # disable interrupts on currently running menu
    current_menu.stop_menu()
    
    # Load new menu based on the id of the selected menu item
    selected_menu_id = current_menu.selectables[new_menu_item]["id"]
    if selected_menu_id in menu_map:
        menu = menu_map[selected_menu_id]()
        return menu
    else:
        print("menu is not valid")
        

def monitor(menu):
    """
    Description: monitors for interrupts across buttons and
    encoder changes and runs functions to update display
    and load new menus.
    """
    while not thread_manager.is_stopped():
        
        # Look for a new job in the auxiliary button queue
        if not queue_handler.is_empty():
            #print("queue not empty")
            item = queue_handler.dequeue()
            menu = get_menu_from_button(item)
            
        # Monitor 1 cycle of encoder position and update display reflected current selection
        menu.poll_selection_change_and_update_display()

        # Monitor for encoder button selection
        if menu.is_encoder_button_pressed():
            # Get the new menu selection
            new_selection = menu.get_selection()
            print(f"encoder button pressed, counter value: {new_selection}")
            
            # Load the menu
            menu = load_menu(menu, new_selection)

        utime.sleep(0.1)        


def start_monitoring(initial_menu):
    def target():
        monitor(initial_menu)
    print("thread monitoring started..")
    thread_manager.start_thread(target)


def stop_monitoring():
    # Probably should not restart thread under normal conditions
    # see display recursion issue in README
    thread_manager.stop_thread()
    thread_manager.wait_for_stop()
    menu.stop_menu()


def mute():
    pass


# Initialize radio power button
def initialize_button(button_pin, led_pin, identity):
    def button_callback(identity):
        # Callback function for button interrupts
        #print(f"button called with identity: {identity}")
        #config = start_volume_config()
        queue_handler.add_to_queue(identity)

    button = Button(
        button_pin=0,
        callback=button_callback,
        led_pin=15,
        debounce_time_ms=10,
        identity='radio_power'
    )
    return button


radio_pwr_button = initialize_button(
    button_pin=0,
    led_pin=15,
    identity="radio_power"
)

# Initialize the second display with a different resolution (e.g., 96x16)
second_display = CR_SPI_Display_Second(
    screen_width=SCREEN2_WIDTH,  # New width
    screen_height=SCREEN2_HEIGHT,  # New height
    spi_dev=SPI_DEVICE2,  # Second SPI device
    spi_sck=10,
    spi_sda=11,
    spi_cs=13,
    res=14,
    dc=12
)

# Create the default menu
main_menu = start_main_menu()

# Start the menu thread with the default menu
start_monitoring(main_menu)

try:
    while True:
        utime.sleep(0.1)

except KeyboardInterrupt:
    queue_handler.add_to_queue("stop_monitoring")
    #stop_monitoring()
    print("Stopped monitoring")
