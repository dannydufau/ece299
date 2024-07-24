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
    menu_map
)
from display_config import create_navigation_display, create_report_display
from context_queue import context_queue
from context import Context

# Initialize the thread manager
thread_manager = ThreadManager()

# Instantiate the auxiliary and reporting queues
#auxiliary_queue = QueueHandler()
#reporting_queue = QueueHandler()


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
    elif id == "snooze":
        menu = start_snooze_config(navigation_display, rtc)
    else:
        # Default to start_main_menu if no match
        menu = start_main_menu(navigation_display)
    return menu


def load_menu(current_menu, context):
    #print(f"load_menu context: {context.router_context}")
    current_menu.stop()
    next_ui_id = context.router_context.get("next_ui_id") if context else None
    
    if next_ui_id:
        
        # Ensure the context is requeued before calling next UI
        context_queue.add_to_queue(context)
        print(f"runner,load_menu,add\n{context.router_context}\n{context.ui_context}\n{context_queue.size()}")

        if next_ui_id == "main_menu":
            new_menu = start_main_menu(navigation_display)
        elif next_ui_id == "new_time":
            new_menu = start_set_time(navigation_display, rtc)
        elif next_ui_id == "set_time":
            new_menu = start_time_config(navigation_display, rtc)
        elif next_ui_id == "set_hour":
            new_menu = start_hour_config(navigation_display, rtc)
        elif next_ui_id == "set_minute":
            new_menu = start_minute_config(navigation_display, rtc)
        elif next_ui_id == "set_seconds":
            new_menu = start_seconds_config(navigation_display, rtc)
        elif next_ui_id == "set_time_mode":
            new_menu = start_time_mode_config(navigation_display, rtc)
        elif next_ui_id == "alarm_menu":
            new_menu = start_alarm_menu(navigation_display)
        elif next_ui_id == "new_alarm":
            new_menu = start_create_alarm(navigation_display, rtc)
        elif next_ui_id == "set_alarm":
            new_menu = start_alarm_config(navigation_display, rtc)
        elif next_ui_id == "list_alarms":
            new_menu = start_list_alarms(navigation_display, rtc)
        elif next_ui_id == "create_alarm":
            new_menu = start_create_alarm(navigation_display, rtc)
        elif next_ui_id == "delete_alarm" and context.ui_context and "alarm_id" in context.ui_context:
            new_menu = start_delete_alarm_config(navigation_display, rtc, context.ui_context["alarm_id"])
        else:
            new_menu = menu_map[next_ui_id](navigation_display)
        
    else:
        raise Exception("No next_ui_id found in context.")

    return new_menu


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
            # Dequeue the context for the next menu
            if context_queue.size() > 0:
                context = context_queue.dequeue()
                #print(f"runner,nav_mon,dequeue\n{context_obj.router_context}\n{context_queue.size()}")
                print(f"runner,nav_mon,dequeue\n{context.router_context}\n{context.ui_context}\n{context_queue.size()}")

                if context:
                    # Load the next menu
                    menu = load_menu(menu, context)

        utime.sleep(0.1)


def start_monitoring(initial_menu):
    def target():
        navigation_monitor(initial_menu)
    
    #print("navigation thread monitoring started..")
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

# Initialize the Timer
timer = Timer()

def timer_callback(timer):
    # Clear the existing display to remove old data
    report_display.clear()
    
    # Check for jobs in the reporting_queue
    if not reporting_queue.is_empty():
        job = reporting_queue.dequeue()
        if job["job_id"] == "snooze_active":
            snooze_message = job["msg"]
            snooze_start_time = utime.time()
            snooze_duration = 5 * 60  # 5 minutes in seconds

    # Get RTC data and update the display
    rtc_data = rtc.get_formatted_datetime_from_module()

    if rtc_data:
        report_display.update_text(rtc_data.get("date"), 0, 1)
        report_display.update_text(rtc_data.get("time"), 0, 2)

    # Get snooze alarm from queue
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
                alarm_disable_context = Context(
                    router_context={"next_ui_id": "alarm_disable"},
                    ui_context={"header": "Disable Alarm"}
                )
                context_queue.add_to_queue(alarm_disable_context)
                auxiliary_queue.add_to_queue("alarm_disable")
            alarm_row_postition += 1

    # Calculate and display snooze countdown if snooze is active
    if 'snooze_start_time' in locals():
        elapsed_time = utime.time() - snooze_start_time
        remaining_time = snooze_duration - elapsed_time
        if remaining_time > 0:
            minutes = int(remaining_time // 60)
            seconds = int(remaining_time % 60)
            snooze_countdown = f"Snooze: {minutes:02d}:{seconds:02d}"
            report_display.update_text(snooze_countdown, 0, alarm_row_postition)
        else:
            # Snooze period has ended
            rtc.alarm_on()
            auxiliary_queue.add_to_queue("alarm_disable")
            del snooze_start_time

# Set the timer to call the callback function every 1 second
timer.init(period=1000, mode=Timer.PERIODIC, callback=timer_callback)


def snooze_button_callback(identity):
    auxiliary_queue.add_to_queue("snooze")

# Initialize the snooze button
snooze_button = Button(
    button_pin=0,  # Assuming pin 21 is used for snooze button
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
