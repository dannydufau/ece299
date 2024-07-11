# runner.py

import utime
from button import Button
from menu import Menu
from thread_manager import ThreadManager
from queue_handler import QueueHandler
from rtc import RTC
from menu_config import start_main_menu, start_hour_config, start_minute_config, start_second_config, start_time_mode_config, menu_map
from display_config import create_navigation_display, create_report_display

# Initialize the thread manager
thread_manager = ThreadManager()

# Instantiate the auxiliary and report queues
auxiliary_queue = QueueHandler()
report_queue = QueueHandler()

# Create the RTC instance
rtc = RTC()

# Initialize the displays
navigation_display = create_navigation_display()
report_display = create_report_display()


def get_menu_from_button(id):
    if id == "radio_power":
        menu = start_volume_config()
    elif id == "start_main_menu":
        menu = start_main_menu(navigation_display)
    elif id == "stop_monitoring":
        thread_manager.stop_thread()
        menu.stop()
        
        # Returning a default menu to avoid None
        return start_main_menu(navigation_display)
    else:
        # Default to start_main_menu if no match
        menu = start_main_menu(navigation_display)
    return menu


def load_menu(current_menu, new_menu_item_id):
    current_menu.stop()
    if new_menu_item_id in menu_map:
        
        # Determine which menu to load
        if new_menu_item_id == "set_hour":
            new_menu = start_hour_config(navigation_display, rtc)
        elif new_menu_item_id == "set_minute":
            new_menu = start_minute_config(navigation_display, rtc)
        elif new_menu_item_id == "set_second":
            new_menu = start_second_config(navigation_display, rtc)
        elif new_menu_item_id == "set_time_mode":
            new_menu = start_time_mode_config(navigation_display, rtc)
        else:
            new_menu = menu_map[new_menu_item_id](navigation_display)

        if isinstance(new_menu, Menu):
            new_menu.poll_selection_change_and_update_display()
        return new_menu
    else:
        print("menu is not valid")
        return current_menu


def monitor(menu):
    while not thread_manager.is_stopped():
        # Check if the auxiliary button was pushed
        if not auxiliary_queue.is_empty():
            item = auxiliary_queue.dequeue()
            menu = get_menu_from_button(item)

        # Check for a time update
        # TODO: do this in main thread?
        if not report_queue.is_empty():
            rtc_data = report_queue.dequeue()
            if rtc_data:
                report_queue.add_to_queue(rtc_data)

        # Check if the encoder rotated
        menu.poll_selection_change_and_update_display()

        # Check if the encoder button was pushed
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


def initialize_button(button_pin, led_pin, identity):
    def button_callback(identity):
        auxiliary_queue.add_to_queue(identity)

    button = Button(
        button_pin=button_pin,
        callback=button_callback,
        led_pin=led_pin,
        debounce_time_ms=10,
        identity=identity
    )
    return button


radio_pwr_button = initialize_button(
    button_pin=0,
    led_pin=15,
    identity="radio_power"
)

main_menu = start_main_menu(navigation_display)

start_monitoring(main_menu)

try:
    while True:
        # Enqueue RTC data to the report queue
        rtc_data = rtc.get_datetime()
        report_queue.add_to_queue(rtc_data)

        # Dequeue RTC data from the report queue and update the display
        if not report_queue.is_empty():
            rtc_data = report_queue.dequeue()
            if rtc_data:
                report_display.update_text(rtc_data.get("date"), 0, 1)
                report_display.update_text(rtc_data.get("time"), 0, 2)

        utime.sleep(1)

except KeyboardInterrupt:
    auxiliary_queue.add_to_queue("stop_monitoring")
    print("Stopped monitoring")
