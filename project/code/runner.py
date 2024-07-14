import utime
from machine import Timer
from button import Button
from menu import Menu
from thread_manager import ThreadManager
from queue_handler import QueueHandler
from rtc import RealTimeClock
from menu_config import start_main_menu, start_hour_config, start_minute_config, start_seconds_config, start_time_mode_config, start_alarm_disable_config, menu_map
from display_config import create_navigation_display, create_report_display

# Initialize the thread manager
thread_manager = ThreadManager()

# Instantiate the auxiliary queue
auxiliary_queue = QueueHandler()

# Create the RTC instance
rtc = RealTimeClock()

# Initialize the displays
navigation_display = create_navigation_display()
report_display = create_report_display()


def get_menu_from_auxiliary(id):
    if id == "radio_power":
        menu = start_volume_config()
    elif id == "start_main_menu":
        menu = start_main_menu(navigation_display)
    elif id == "stop_monitoring":
        thread_manager.stop_thread()
        menu.stop()
        
        # Returning a default menu to avoid None
        return start_main_menu(navigation_display)
    elif id == "alarm_disable":
        menu = start_alarm_disable_config(navigation_display, rtc)
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
        elif new_menu_item_id == "set_seconds":
            new_menu = start_seconds_config(navigation_display, rtc)
        elif new_menu_item_id == "set_time_mode":
            new_menu = start_time_mode_config(navigation_display, rtc)
        elif new_menu_item_id == "set_hour_alarm":
            new_menu = start_hour_config(
                display=navigation_display,
                rtc=rtc,
                time_or_alarm="alarm",
                next_config={"id": "set_minute_alarm", "display_text": "Set Alarm Minutes"}
            )
        elif new_menu_item_id == "set_minute_alarm":
            new_menu = start_minute_config(
                display=navigation_display,
                rtc=rtc,
                time_or_alarm="alarm",
                next_config={"id": "set_seconds_alarm", "display_text": "Set Alarm Seconds"}
            )
        elif new_menu_item_id == "set_seconds_alarm":
            new_menu = start_seconds_config(
                display=navigation_display,
                rtc=rtc,
                time_or_alarm="alarm"
            )
        else:
            new_menu = menu_map[new_menu_item_id](navigation_display)

        print(f"menu: {new_menu}")
        if isinstance(new_menu, Menu):
            new_menu.poll_selection_change_and_update_display()
        return new_menu
    else:
        print(f"menu is not valid: {new_menu_item_id}")
        return current_menu


def navigation_monitor(menu):
    while not thread_manager.is_stopped():
        
        # Check if the auxiliary button was pushed for menu request
        if not auxiliary_queue.is_empty():
            item = auxiliary_queue.dequeue()
            print(f"alarm should dequeue...{item}")
            menu = get_menu_from_auxiliary(item)

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
        navigation_monitor(initial_menu)
    print("navigation thread monitoring started..")
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
# Initialize the Timer
timer = Timer()


def timer_callback(timer):
    # Get RTC data and update the display
    rtc_data = rtc.get_formatted_datetime_from_module()
    if rtc_data:
        report_display.update_text(rtc_data.get("date"), 0, 1)
        report_display.update_text(rtc_data.get("time"), 0, 2)

    # Get the alarm time and update the display
    alarm_time = rtc.get_alarm_time()
    alarm_text = "Alarm: {:02d}:{:02d}:{:02d}".format(alarm_time['hour'], alarm_time['minute'], alarm_time['second'])
    report_display.update_text(alarm_text, 0, 3)

    # Check if the current time matches the alarm time
    if (rtc_data["hour"] == alarm_time["hour"] and 
        rtc_data["minute"] == alarm_time["minute"] and 
        rtc_data["second"] == alarm_time["second"]):
        rtc.alarm_on()
        # Enqueue the alarm disable config job
        print("alarm should go on!!")
        auxiliary_queue.add_to_queue("alarm_disable")

# Set the timer to call the callback function every 1 second
timer.init(period=1000, mode=Timer.PERIODIC, callback=timer_callback)

try:
    while True:
        utime.sleep(0.1)  # Or handle other non-blocking tasks here
except KeyboardInterrupt:
    auxiliary_queue.add_to_queue("stop_monitoring")
    rtc.alarm_off()
    timer.deinit()
    print("Stopped monitoring")

