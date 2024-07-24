import utime
from machine import Timer
from button import Button
from menu import Menu
from thread_manager import ThreadManager
from rtc import RealTimeClock
from menu_config import (
    start_main_menu,
    start_set_time,
    start_time_config,
    start_hour_config,
    start_minute_config,
    start_seconds_config,
    start_time_mode_config,
    start_alarm_disable_config,
    start_alarm_menu,
    start_list_alarms,
    start_create_alarm,
    start_alarm_config,
    start_delete_alarm_config,
    start_snooze_config,
    menu_map,
    auxiliary_menu_map
)
from display_config import create_navigation_display, create_report_display
from context_queue import context_queue, auxiliary_queue, reporting_queue
from context import Context

# Initialize the thread manager
thread_manager = ThreadManager()

# Create the RTC instance
rtc = RealTimeClock()

# Clear stale data
rtc.delete_all_snooze_files()

# Initialize the displays
navigation_display = create_navigation_display()
report_display = create_report_display()


def get_menu_from_auxiliary(id):
    if id in auxiliary_menu_map:
        # Handle special case for stopping monitoring
        if id == "stop_monitoring":
            thread_manager.stop_thread()
            menu.stop()
            return start_main_menu(navigation_display)
        
        # Call the corresponding function from auxiliary_menu_map
        if id in ["alarm_disable", "snooze"]:
            menu = auxiliary_menu_map[id](navigation_display, rtc)
        else:
            menu = auxiliary_menu_map[id](navigation_display)
    else:
        # Default to start_main_menu if no match
        menu = start_main_menu(navigation_display)
    
    return menu


def load_menu(current_menu, context):
    current_menu.stop()
    next_ui_id = context.router_context.get("next_ui_id") if context else None
    
    if next_ui_id:
        
        # Ensure the context is requeued before calling next UI
        context_queue.add_to_queue(context)
        print(f"runner,load_menu,add\n{context.router_context}\n{context.ui_context}\n{context_queue.size()}")

        # Check if the next_ui_id is in the menu_map
        if next_ui_id in menu_map:

            # Call the corresponding function from menu_map
            if next_ui_id == "delete_alarm" and context.ui_context and "alarm_id" in context.ui_context:
                new_menu = menu_map[next_ui_id](navigation_display, rtc, context.ui_context["alarm_id"])
            elif next_ui_id in ["new_time", "set_time", "set_hour", "set_minute", "set_seconds", "set_time_mode", "new_alarm", "set_alarm", "list_alarms"]:
                new_menu = menu_map[next_ui_id](navigation_display, rtc)
            else:
                new_menu = menu_map[next_ui_id](navigation_display)
        else:
            raise Exception(f"Invalid next_ui_id: {next_ui_id}")

    else:
        raise Exception("No next_ui_id found in context.")

    return new_menu


def navigation_monitor(menu):
    while not thread_manager.is_stopped():
        
        # Check if the auxiliary button was pushed for menu request
        if not auxiliary_queue.is_empty():
            item = auxiliary_queue.dequeue()
            #print(f"alarm should dequeue...{item}")
            menu = get_menu_from_auxiliary(item)

        # Check if the encoder rotated
        menu.poll_selection_change_and_update_display()

        # Check if the encoder button was pushed
        if menu.is_encoder_button_pressed():
            # Dequeue the context for the next menu
            if context_queue.size() > 0:
                context = context_queue.dequeue()
                print(f"runner,nav_mon,dequeue\n{context.router_context}\n{context.ui_context}\n{context_queue.size()}")

                if context:
                    # Load the next menu
                    menu = load_menu(menu, context)

        utime.sleep(0.1)


def start_monitoring(initial_menu):
    def target():
        navigation_monitor(initial_menu)
    
    thread_manager.start_thread(target)

# Initialize the initial menu with the context
main_menu_context = Context(
    router_context={"next_ui_id": "main_menu"},
    ui_context={
        "header": "Main Menu",
        "selectables": [
            {"display_text": "Time", "id": "time_menu"},
            {"display_text": "Radio", "id": "radio_menu"}
        ]
    }
)
context_queue.add_to_queue(main_menu_context)
main_menu = Menu(
    display=navigation_display,
    encoder_pins=(19, 18, 20),
    led_pin=15,
    id="main_menu"
)

start_monitoring(main_menu)


def timer_callback(timer):
    # Clear the existing display to remove old data
    report_display.clear()

    # Get RTC data and update the display
    rtc_data = rtc.get_formatted_datetime_from_module()

    if rtc_data:
        report_display.update_text(rtc_data.get("date"), 0, 1)
        report_display.update_text(rtc_data.get("time"), 0, 2)

    # Get the snooze time and display it if active
    snooze = rtc.get_snooze_time()
    
    if snooze:
        snooze_id, snooze_time = snooze[0]
        snooze_text = "Snooze: {:02d}:{:02d}:{:02d}".format(
            snooze_time['hour'], snooze_time['minute'], snooze_time['second'])
        report_display.update_text(snooze_text, 0, 3)

        # Check if the current time matches the snooze time
        if (rtc_data["hour"] == snooze_time["hour"] and 
            rtc_data["minute"] == snooze_time["minute"] and 
            rtc_data["second"] == snooze_time["second"]):
            rtc.alarm_on()
            auxiliary_queue.add_to_queue("alarm_disable")
            rtc.delete_all_snooze_files()
        return  # Return early if snooze is active

    # Get all alarm times
    alarm_times = rtc.get_all_alarm_times()
    #print(f"ALARMS: {alarm_times}")
    alarm_row_position = 3
    if alarm_times:
        for alarm_id, alarm_time in alarm_times:
            alarm_text = "Alarm: {:02d}:{:02d}:{:02d}".format(
                alarm_time['hour'], alarm_time['minute'], alarm_time['second'])
            report_display.update_text(alarm_text, 0, alarm_row_position)

            # Check if the current time matches the alarm time
            if (rtc_data["hour"] == alarm_time["hour"] and 
                rtc_data["minute"] == alarm_time["minute"] and 
                rtc_data["second"] == alarm_time["second"]):
                rtc.alarm_on()
                # Enqueue the alarm disable config job
                print(f"alarm should go on!! {rtc.is_alarm_active()}")
                alarm_disable_context = Context(
                    router_context={"next_ui_id": "alarm_disable"},
                    ui_context={"header": "Disable Alarm"}
                )
                context_queue.add_to_queue(alarm_disable_context)
                auxiliary_queue.add_to_queue("alarm_disable")

            alarm_row_position += 1


# Initialize the Timer
timer = Timer()
# Set the timer to call the callback function every 1 second
timer.init(period=1000, mode=Timer.PERIODIC, callback=timer_callback)


def snooze_button_callback(identity):
    auxiliary_queue.add_to_queue("snooze")

# Initialize the snooze button
snooze_button = Button(
    button_pin=0,  # Assuming pin 0 is used for snooze button
    led_pin=15,   # No LED associated
    callback=snooze_button_callback,
    identity="snooze",
    debounce_time_ms=10
)

try:
    while True:
        utime.sleep(0.1)

except KeyboardInterrupt:
    auxiliary_queue.add_to_queue("stop_monitoring")
    rtc.alarm_off()
    timer.deinit()
    print("Stopped monitoring")
