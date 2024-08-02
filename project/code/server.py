# TODO: event loop pattern
import utime
import time  # need this strangely or we get strange conflict w/ utime when importing radio_control
from machine import Timer
from button import Button
from menu import Menu
from thread_manager import ThreadManager
from rtc import RealTimeClock
from menu_config import (
    start_main_menu,
    start_volume_config,
    menu_map,
    auxiliary_menu_map,
)

from display_config import create_navigation_display, create_report_display
from context_queue import context_queue, auxiliary_queue
from context import Context
from radio_control import RadioControl
from logger import Logger

# print(f"recursion limit: {sys.getrecursionlimit()}")
# MicroPython's recursion depth is inherently limited by the available stack space of the microcontroller.
# The recursion depth limit for MicroPython on the Raspberry Pi Pico is approximately 20 to 30 levels. This is significantly lower than the default limit in standard Python, which is around 1000 levels. The exact limit can vary depending on the specific implementation and available memory​ (Stack Overflow)​​ (MicroPython Forum)​.
# https://forum.micropython.org/viewtopic.php?t=3091

# Initialize the logger
logger = Logger(level=Logger.INFO)

# Initialize the thread manager
thread_manager = ThreadManager()

# Create the RTC instance
rtc = RealTimeClock()

# Clear stale data
rtc.delete_all_snooze_files()

# Initialize the displays
navigation_display = create_navigation_display()
report_display = create_report_display()

radio_control = RadioControl()

# Store time since boot to display boot messages
boot_time = utime.time()


def get_menu_from_auxiliary(id, rtc):
    """
    Loads menus from auxiliary buttons.
    """
    try:
        if id in auxiliary_menu_map:

            # Handle special case for stopping monitoring
            if id == "stop_monitoring":
                rtc.alarm_off()
                thread_manager.stop_thread()
                menu.stop()
                return start_main_menu(navigation_display)

            elif id == "radio_power":
                rtc.alarm_off()
                radio_control.toggle_mute()
                if radio_control.muted:
                    return start_main_menu(navigation_display)
                else:
                    return start_volume_config(
                        navigation_display, radio_control
                    )  # Show volume config as a placeholder

            if id in ["alarm_disable", "snooze"]:
                menu = auxiliary_menu_map[id](navigation_display, rtc)
            else:
                menu = auxiliary_menu_map[id](navigation_display)
        else:
            # Default to start_main_menu if no match
            menu = start_main_menu(navigation_display)

        return menu

    except Exception as e:
        msg = "Error in get_menu_from_auxiliary"
        logger.error(e, msg)


def load_menu(current_menu, context, rtc):
    """ """
    try:
        current_menu.stop()
        next_ui_id = context.router_context.get("next_ui_id") if context else None

        if next_ui_id:

            # Ensure the context is requeued before calling next UI
            context_queue.add_to_queue(context)
            # logger.debug(f"server,load_menu,add\n{context.router_context}\n{context.ui_context}\n{context_queue.size()}")

            # Check if the next_ui_id is in the menu_map
            if next_ui_id in menu_map:

                # Call the corresponding function from menu_map
                if (
                    next_ui_id == "delete_alarm"
                    and context.ui_context
                    and "alarm_id" in context.ui_context
                ):
                    new_menu = menu_map[next_ui_id](
                        navigation_display, rtc, context.ui_context["alarm_id"]
                    )
                elif next_ui_id in [
                    "set_volume",
                    "set_frequency",
                    "frequency_fractional",
                ]:
                    new_menu = menu_map[next_ui_id](navigation_display, radio_control)
                elif next_ui_id in [
                    "new_date",
                    "set_date",
                    "new_time",
                    "set_time",
                    "set_hour",
                    "set_timezone",
                    "set_minute",
                    "set_seconds",
                    "set_time_mode",
                    "new_alarm",
                    "set_alarm",
                    "list_alarms",
                ]:
                    new_menu = menu_map[next_ui_id](navigation_display, rtc)
                else:
                    new_menu = menu_map[next_ui_id](navigation_display)
            else:
                raise Exception(f"Invalid next_ui_id: {next_ui_id}")

        else:
            raise Exception("No next_ui_id found in context.")

        return new_menu

    except Exception as e:
        msg = "Error in load_menu"
        logger.error(e, msg)


def navigation_monitor(menu, auxiliary_queue, thread_manager, rtc):
    import utime  # hack! - Unclear why global import not in scope

    try:
        while not thread_manager.is_stopped():
            # Check if the auxiliary button was pushed for menu request
            if not auxiliary_queue.is_empty():
                item = auxiliary_queue.dequeue()
                menu = get_menu_from_auxiliary(item, rtc)

            # Check if the encoder rotated
            menu.poll_selection_change_and_update_display()

            # Dequeue the context for the next menu
            if context_queue.size() > 0:
                context = context_queue.dequeue()
                logger.debug(
                    f"runner,nav_mon,dequeue\n{context.router_context}\n{context.ui_context}\n{context_queue.size()}"
                )

                if context:
                    # Load the next menu
                    menu = load_menu(menu, context, rtc)

                utime.sleep(0.1)

    except Exception as e:
        msg = "Error in navigation_monitor"
        logger.error(e, msg)


def start_monitoring(initial_menu, auxiliary_queue, thread_manager, rtc):
    def target():
        navigation_monitor(initial_menu, auxiliary_queue, thread_manager, rtc)

    try:
        thread_manager.start_thread(target)

    except Exception as e:
        msg = "Error in starting thread in start_monitoring"
        logger.error(e, msg)


try:
    # Initialize the initial menu with the context
    main_menu_context = Context(
        router_context={"next_ui_id": "main_menu"},
        ui_context={
            "header": "Main Menu",
            "selectables": [
                {"display_text": "Date", "id": "date_menu"},
                {"display_text": "Time", "id": "time_menu"},
                {"display_text": "Radio", "id": "radio_menu"},
            ],
        },
    )

    context_queue.add_to_queue(main_menu_context)
    main_menu = Menu(
        display=navigation_display,
        encoder_pins=(19, 18, 20),
        led_pin=15,
        id="main_menu",
    )
    start_monitoring(main_menu, auxiliary_queue, thread_manager, rtc)

except Exception as e:
    msg = "Error in main thread starting navigation thread"
    logger.error(e, msg)


def display_battery_status():
    try:
        voltage = rtc.read_battery_voltage()
        battery_status = rtc.get_battery_status()
        battery_text = "Battery: {:.2f}V".format(voltage)
        report_display.update_text(battery_text, 0, 0)
        report_display.update_text(battery_status, 0, 1)

    except Exception as e:
        msg = "Error in display_battery_status"
        logger.error(e, msg)


def display_radio_status():
    try:
        # Check if the radio is muted and display the current frequency
        if not radio_control.muted:
            current_frequency = radio_control.get_frequency()
            current_volume = radio_control.get_volume()
            radio_status_text = "{:.1f}MHz Vol: {}".format(
                current_frequency, current_volume
            )
            report_display.update_text(radio_status_text, 0, 3)

        else:
            report_display._clear_row(3)

    except Exception as e:
        msg = "Error in display_radio_status"
        logger.error(e, msg)


def display_datetime_status():
    try:
        rtc_data = rtc.get_formatted_datetime_from_module()

        if rtc_data:
            date = rtc_data.get("date")
            zone = rtc_data.get("timezone")
            report_display.update_text(f"{date}-{zone}", 0, 1)
            report_display.update_text(rtc_data.get("time"), 0, 2)

    except Exception as e:
        msg = "Error in display_time_status"
        logger.error(e, msg)


def display_snooze_status(auxiliary_queue):
    try:
        rtc_data = rtc.get_formatted_datetime_from_module()
        snooze = rtc.get_snooze_time()

        if snooze:
            snooze_id, snooze_time = snooze[0]
            snooze_text = "Snooze: {:02d}:{:02d}:{:02d}".format(
                snooze_time["hour"], snooze_time["minute"], snooze_time["second"]
            )
            report_display._clear_row(4)
            report_display.update_text(snooze_text, 0, 4)

            # Check if the current time matches the snooze time
            if (
                rtc_data["hour"] == snooze_time["hour"]
                and rtc_data["minute"] == snooze_time["minute"]
                and rtc_data["second"] == snooze_time["second"]
            ):
                rtc.alarm_on()
                auxiliary_queue.add_to_queue("alarm_disable")
                rtc.delete_all_snooze_files()
            return True
        return False

    except Exception as e:
        msg = "Error in display_snooze_status"
        logger.error(e, msg)


def display_alarm_status(auxiliary_queue):
    try:
        rtc_data = rtc.get_formatted_datetime_from_module()
        alarm_times = rtc.get_all_alarm_times()

        alarm_row_position = 4

        if alarm_times:
            for alarm_id, alarm_time in alarm_times:
                alarm_text = "Alarm: {:02d}:{:02d}:{:02d}".format(
                    alarm_time["hour"], alarm_time["minute"], alarm_time["second"]
                )

                # report_display._clear_row(alarm_row_position)
                report_display.update_text(alarm_text, 0, alarm_row_position)

                # Check if the current time matches the alarm time
                if (
                    rtc_data["hour"] == alarm_time["hour"]
                    and rtc_data["minute"] == alarm_time["minute"]
                    and rtc_data["second"] == alarm_time["second"]
                ):
                    rtc.alarm_on()

                    # Enqueue the alarm disable config job
                    logger.debug(f"alarm should go on!! {rtc.is_alarm_active()}")
                    alarm_disable_context = Context(
                        router_context={"next_ui_id": "alarm_disable"},
                        ui_context={"header": "Disable Alarm"},
                    )
                    context_queue.add_to_queue(alarm_disable_context)
                    auxiliary_queue.add_to_queue("alarm_disable")

                alarm_row_position += 1
        else:
            report_display._clear_row(4)

    except Exception as e:
        msg = "Error in display_alarm_status"
        logger.error(e, msg)


def boot_messages():
    display_battery_status()


def timer_callback(timer, auxiliary_queue):
    try:
        current_time = utime.time()

        # Display battery status for the first 5 seconds
        if current_time - boot_time < 5:
            boot_messages()

        else:
            report_display._clear_row(
                0
            )  # Clear the battery status display after 5 seconds
            report_display._clear_row(
                1
            )  # Clear the battery status display after 5 seconds

            # Check if the radio is muted and display the current frequency
            display_radio_status()

            # Get RTC data and update the display
            display_datetime_status()

            # Get the snooze time and display it if active
            if display_snooze_status(auxiliary_queue):
                return  # Return early if snooze is active

            # Get all alarm times
            display_alarm_status(auxiliary_queue)

    except Exception as e:
        msg = "Error in timer_callback"
        print(f"{msg}\n{e}")
        # logger.error(e, msg)


try:
    # Initialize the Timer
    timer = Timer()

    # Set the timer to call the callback function every 1 second and pass in aux_queue
    timer.init(
        period=1000,
        mode=Timer.PERIODIC,
        callback=lambda t: timer_callback(t, auxiliary_queue),
    )

except Exception as e:
    msg = "Error in main thread initializing timer_callback"
    logger.error(e, msg)


def snooze_button_callback(identity, auxiliary_queue):
    auxiliary_queue.add_to_queue(identity)


# Initialize the snooze button
# TODO: NOT ACTIVE!!!!!!!!
"""
snooze_button = Button(
    button_pin=0, #0 on bb 9 on pcb
    led_pin=15, # 15 on bb 8 on pcb
    callback=snooze_button_callback,
    identity="snooze",
    debounce_time_ms=10,
    auxiliary_queue=auxiliary_queue
)
"""


def radio_button_callback(identity, auxiliary_queue):
    auxiliary_queue.add_to_queue(identity)


radio_pwr_button = Button(
    button_pin=0,  # 0 on bb, 15 on pcb
    led_pin=15,  # 15 on bb, 8 on pcb
    callback=radio_button_callback,
    identity="radio_power",
    debounce_time_ms=10,
    auxiliary_queue=auxiliary_queue,
)


try:
    while True:
        utime.sleep(0.1)

except KeyboardInterrupt:
    auxiliary_queue.add_to_queue("stop_monitoring")
    rtc.alarm_off()
    timer.deinit()
    logger.info("Stopped monitoring")

except Exception as e:
    logger.error(e, "main loop error")
