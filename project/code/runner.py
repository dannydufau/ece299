import utime
from machine import Timer
from button import Button
from menu import Menu
from thread_manager import ThreadManager
from queue_handler import QueueHandler
from rtc import RealTimeClock
from menu_config import (
    start_main_menu,
    start_hour_config,
    start_minute_config,
    start_seconds_config,
    start_time_mode_config,
    start_alarm_disable_config,
    start_alarm_hour_config,
    start_alarm_minute_config,
    start_alarm_seconds_config,
    start_alarm_menu,
    start_list_alarms,
    start_create_alarm,
    menu_map
)
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
        menu = start_volume_config(navigation_display)
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


def load_menu(current_menu, new_menu_item_id, context=None):
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
            new_menu = start_alarm_hour_config(
                display=navigation_display,
                rtc=rtc,
                alarm_id=context.get("alarm_id"),
                next_config={"id": "set_minute_alarm", "display_text": "Set Alarm Minutes"}
            )
        elif new_menu_item_id == "set_minute_alarm":
            new_menu = start_alarm_minute_config(
                display=navigation_display,
                rtc=rtc,
                alarm_id=context.get("alarm_id"),
                next_config={"id": "set_seconds_alarm", "display_text": "Set Alarm Seconds"}
            )
        elif new_menu_item_id == "set_seconds_alarm":
            new_menu = start_alarm_seconds_config(
                display=navigation_display,
                rtc=rtc,
                alarm_id=context.get("alarm_id")
            )
        elif new_menu_item_id == "alarm_menu":
            new_menu = start_alarm_menu(navigation_display)
        elif new_menu_item_id == "list_alarms":
            new_menu = start_list_alarms(navigation_display, rtc)
        elif new_menu_item_id == "create_alarm":
            new_menu = start_create_alarm(navigation_display, rtc)
        else:
            new_menu = menu_map[new_menu_item_id](navigation_display)

        print(f"menu: {new_menu.header}")
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
            context_data = menu.get_context()
            if context_data:
                new_selection = context_data["id"]
                context = context_data.get("context", {})
                print(f"encoder button pressed, selection: {new_selection}, context: {context}")
                menu = load_menu(menu, new_selection, context)

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

    # Get the alarm times and update the display
    # TODO: don't save duplicate alarms
    alarm_times = rtc.get_alarm_times()
    alarm_row_postition = 3
    if alarm_times:
        for alarm_id, alarm_time in alarm_times:
            alarm_text = "Alarm: {:02d}:{:02d}:{:02d}".format(
                alarm_time['hour'], alarm_time['minute'], alarm_time['second'])
            report_display.update_text(alarm_text, 0, alarm_row_postition)

            # Check if the current time matches the alarm time
            if (rtc_data["hour"] == alarm_time["hour"] and 
                rtc_data["minute"] == alarm_time["minute"] and 
                rtc_data["second"] == alarm_time["second"]):
                rtc.alarm_on()
                # Enqueue the alarm disable config job
                print("alarm should go on!!")
                auxiliary_queue.add_to_queue("alarm_disable")
            alarm_row_postition += 1
    else:
        # show no alarm set
        pass

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
