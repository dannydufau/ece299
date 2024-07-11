import utime
from menu import Menu
from button import Button
from thread_manager import ThreadManager
from queue_handler import queue_handler
from display import CR_SPI_Display, CR_SPI_Display_Second
from rtc import RTC
from time_config import TimeConfig


SCREEN_WIDTH = 128
SCREEN_HEIGHT = 64
SPI_DEVICE = 0

REPORT_SCREEN_WIDTH = 128
REPORT_SCREEN_HEIGHT = 64
SPI_DEVICE_REPORT = 1

# Initialize the thread manager
thread_manager = ThreadManager()


def get_list_from_range(low, high):
    return [str(i) for i in range(low, high)]


def create_navigation_display():
    return CR_SPI_Display(
        screen_width=SCREEN_WIDTH,
        screen_height=SCREEN_HEIGHT,
        spi_dev=SPI_DEVICE,
        spi_sck=2,
        spi_sda=3,
        spi_cs=5,
        res=4,
        dc=6
    )


def create_report_display():
    return CR_SPI_Display_Second(
        screen_width=REPORT_SCREEN_WIDTH,
        screen_height=REPORT_SCREEN_HEIGHT,
        spi_dev=SPI_DEVICE_REPORT,
        spi_sck=10,
        spi_sda=11,
        spi_cs=13,
        res=14,
        dc=12
    )


# Menu configuration
def start_volume_config():
    display = create_navigation_display()
    return Menu(
        display=display,
        encoder_pins=(19, 18, 20),
        led_pin=15,
        header="Set the Volume",
        selectables=get_list_from_range(1, 5),
        id="set_volume"
    )

def start_hour_config():
    display = create_navigation_display()
    return TimeConfig(
        display=display,
        encoder_pins=(19, 18, 20),
        led_pin=15,
        header="Hour",
        next_config={"id": "set_minute", "display_text": "Set Minutes"},
        min=1,
        max=12 # TODO: support military time
    )

def start_minute_config():
    display = create_navigation_display()
    return TimeConfig(
        display=display,
        encoder_pins=(19, 18, 20),
        led_pin=15,
        header="Minute",
        next_config={"id": "set_second", "display_text": "Set Seconds"}
    )

def start_second_config():
    display = create_navigation_display()
    return TimeConfig(
        display=display,
        encoder_pins=(19, 18, 20),
        led_pin=15,
        header="Second",
        next_config={"id": "main_menu", "display_text": "Main Menu"}
    )


def start_alarm_config():
    display = create_navigation_display()
    return Menu(
        display=display,
        encoder_pins=(19, 18, 20),
        led_pin=15,
        header="Set the alarm",
        selectables=[
            {"display_text": "Hours", "id": "hours"},
            {"display_text": "Minutes", "id": "minutes"},
            {"display_text": "Seconds", "id": "seconds"}
        ],
        id="set_alarm"
    )


def start_time_menu():
    display = create_navigation_display()
    return Menu(
        display=display,
        encoder_pins=(19, 18, 20),
        led_pin=15,
        header="Time Menu",
        selectables=[
            {"display_text": "set time", "id": "set_hour"},
            {"display_text": "set alarm", "id": "set_alarm"}
        ],
        id="time_menu"
    )


def start_radio_menu():
    display = create_navigation_display()
    return Menu(
        display=display,
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
    display = create_navigation_display()
    return Menu(
        display=display,
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
    "set_hour": start_hour_config,
    "set_minute": start_minute_config,
    "set_second": start_second_config,
    "set_alarm": start_alarm_config,
    "time_menu": start_time_menu,
    "radio_menu": start_radio_menu,
    "main_menu": start_main_menu
}


def get_menu_from_button(id):
    if id == "radio_power":
        menu = start_volume_config()
    elif id == "start_main_menu":
        menu = start_main_menu()
    elif id == "stop_monitoring":
        thread_manager.stop_thread()
        menu.stop()
        return
    return menu


def load_menu(current_menu, new_menu_item_id):
    current_menu.stop()
    if new_menu_item_id in menu_map:
        new_menu = menu_map[new_menu_item_id]()
        # TODO: not using this instance check currently
        if isinstance(new_menu, Menu):
            new_menu.poll_selection_change_and_update_display()
        return new_menu
    else:
        print("menu is not valid")
        return current_menu


# indicate when RTC updates are allowed
rtc_update_allowed = True

def monitor(menu):
    global rtc_update_allowed

    rtc = RTC()
    report_display = create_report_display()

    while not thread_manager.is_stopped():
        if not queue_handler.is_empty():
            item = queue_handler.dequeue()
            menu = get_menu_from_button(item)
        
        menu.poll_selection_change_and_update_display()
        
        if menu.is_encoder_button_pressed():
            rtc_update_allowed = False  # Disable RTC updates when setting time
            new_selection = menu.get_selection()
            print(f"encoder button pressed, counter value: {new_selection}")
            menu = load_menu(menu, new_selection["id"])
            menu.update_display()
            rtc_update_allowed = True  # Re-enable RTC updates after setting time
        
        # Update the RTC display if allowed
        if rtc_update_allowed:
            rtc_data = rtc.get_datetime()
            report_display.update_text(rtc_data.get("date"), 0, 1)
            report_display.update_text(rtc_data.get("time"), 0, 2)
        
        utime.sleep(0.1)


def monitorBak(menu):
    while not thread_manager.is_stopped():
        if not queue_handler.is_empty():
            item = queue_handler.dequeue()
            menu = get_menu_from_button(item)
        
        menu.poll_selection_change_and_update_display()
        
        if menu.is_encoder_button_pressed():
            new_selection = menu.get_selection()
            print(f"encoder button pressed, counter value: {new_selection}")
            menu = load_menu(menu, new_selection["id"])
        
        utime.sleep(0.1)


def start_monitoring(initial_menu):
    def target():
        monitor(initial_menu)
    print("thread monitoring started..")
    thread_manager.start_thread(target)


def stop_monitoring():
    thread_manager.stop_thread()
    thread_manager.wait_for_stop()
    menu.stop()


def mute():
    pass


def initialize_button(button_pin, led_pin, identity):
    def button_callback(identity):
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

report_display = create_report_display()

main_menu = start_main_menu()

start_monitoring(main_menu)

'''
rtc = RTC()

try:
    while True:
        rtc_data = rtc.get_datetime()
        report_display.update_text(rtc_data.get("date"), 0, 1)
        report_display.update_text(rtc_data.get("time"), 0, 2)
        utime.sleep(0.1)

except KeyboardInterrupt:
    queue_handler.add_to_queue("stop_monitoring")
    print("Stopped monitoring")
'''
