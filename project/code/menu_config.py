from menu import Menu
from time_config import TimeConfig
from date_config import DateConfig
from time_mode import TimeMode
from timezone_config import TimeZoneConfig
from alarm_config import AlarmConfig
from alarm_disable import AlarmDisable
from alarm_delete import AlarmDelete
from alarm_snooze import AlarmSnooze
from volume_config import VolumeConfig
from frequency_config import FrequencyConfig
from context_queue import context_queue
from context import Context


def get_list_from_range(low, high):
    return [str(i) for i in range(low, high)]


def start_date_menu(display):
    context = context_queue.dequeue()
    context.router_context["next_ui_id"] = "date_menu"
    context.ui_context.update(
        {
            "header": "Date Menu",
            "selectables": [
                {"display_text": "Set Date", "id": "new_date"},
                {"display_text": "Set Timezone", "id": "set_timezone"},
            ],
        }
    )
    context_queue.add_to_queue(context)
    return Menu(display, encoder_pins=(19, 18, 20), led_pin=15, id="date_menu")


def start_time_menu(display):
    context = context_queue.dequeue()
    context.router_context["next_ui_id"] = "time_menu"
    context.ui_context.update(
        {
            "header": "Time Menu",
            "selectables": [
                {"display_text": "Set Time", "id": "new_time"},
                {"display_text": "Alarm Menu", "id": "alarm_menu"},
                {"display_text": "Set Time Mode", "id": "set_time_mode"},
                # {"display_text": "Set Timezone", "id": "set_timezone"},
            ],
        }
    )
    context_queue.add_to_queue(context)
    return Menu(display, encoder_pins=(19, 18, 20), led_pin=15, id="time_menu")


def start_alarm_disable_config(display, rtc):
    return AlarmDisable(
        display=display,
        rtc=rtc,
        encoder_pins=(19, 18, 20),
        led_pin=15,
    )


def start_snooze_config(display, rtc):
    # Just return the main menu if the alarm isn't triggered
    print(f"start_snooze_config {rtc.is_alarm_active()}")
    if not rtc.is_alarm_active():
        context = Context(
            router_context={"next_ui_id": "main_menu"},
            ui_context={
                "header": "Main Menu",
                "selectables": [
                    {"display_text": "Time", "id": "time_menu"},
                    {"display_text": "Radio", "id": "radio_menu"},
                ],
            },
        )
        context_queue.add_to_queue(context)
        return start_main_menu(display)

    # Otherwise return the snooze alarm config
    context = Context(
        router_context={"next_ui_id": "main_menu"},
        ui_context={"header": "Disable Snooze?", "min": 0, "max": 1, "snooze": True},
    )
    context_queue.add_to_queue(context)
    return AlarmSnooze(
        display=display,
        rtc=rtc,
        encoder_pins=(19, 18, 20),
        led_pin=15,
    )


def start_volume_config(display, radio_control):
    current_context = context_queue.dequeue()
    context = Context(
        router_context={"next_ui_id": "main_menu"},
        ui_context={
            "header": "Volume Setting",
            "min": 0,
            "max": 15,  # Adjusted the range for volume settings (0-15)
        },
    )
    context_queue.add_to_queue(context)

    return VolumeConfig(
        display=display,
        radio_control=radio_control,
        encoder_pins=(19, 18, 20),
        led_pin=15,
        id="set_volume",
    )


def start_list_alarms(display, rtc):
    current_context = context_queue.dequeue()

    alarms = rtc.get_alarm_times()
    selectables = [
        {
            "display_text": f"{alarm[1]['hour']:02d}:{alarm[1]['minute']:02d}:{alarm[1]['second']:02d}",
            "id": "delete_alarm",
            "context": {"alarm_id": alarm[0]},
        }
        for alarm in alarms
    ] or [{"display_text": "No alarms set", "id": "main_menu"}]

    context = Context(
        router_context={"next_ui_id": "list_alarms"},
        ui_context={"header": "Alarm Delete", "selectables": selectables},
    )

    context_queue.add_to_queue(context)
    return Menu(display, encoder_pins=(19, 18, 20), led_pin=15, id="list_alarms")


def start_delete_alarm_config(display, rtc, alarm_id):
    return AlarmDelete(
        display=display,
        rtc=rtc,
        encoder_pins=(19, 18, 20),
        led_pin=15,
        alarm_id=alarm_id,
    )


def start_alarm_config(display, rtc):
    return AlarmConfig(
        display=display,
        rtc=rtc,
        encoder_pins=(19, 18, 20),
        led_pin=15,
    )


def start_create_alarm(display, rtc):
    # Init alarm set process.
    # called from menu.py which wont know about context
    context = context_queue.dequeue()
    context.router_context["next_ui_id"] = "set_hour"
    context.ui_context.update({"header": "hour", "min": 0, "max": 24})
    context_queue.add_to_queue(context)
    return start_alarm_config(display, rtc)


def start_alarm_menu(display):
    context = context_queue.dequeue()
    context.router_context["next_ui_id"] = "alarm_menu"
    context.ui_context.update(
        {
            "header": "Alarm Menu",
            "selectables": [
                {"display_text": "New Alarm", "id": "new_alarm"},
                {"display_text": "List", "id": "list_alarms"},
            ],
        }
    )
    context_queue.add_to_queue(context)
    return Menu(display, encoder_pins=(19, 18, 20), led_pin=15, id="alarm_menu")


def start_time_mode_config(display, rtc):
    return TimeMode(
        display=display,
        rtc=rtc,
        encoder_pins=(19, 18, 20),
        led_pin=15,
        header="Time Mode",
    )


def start_timezone_config(display, rtc):
    context = context_queue.dequeue()
    context.router_context["next_ui_id"] = "time_menu"
    context.ui_context.update(
        {
            "header": "Time Menu",
            "selectables": [
                # {"display_text": "UTC", "id": "UTC"},
                {"display_text": "CST", "id": "CST"},
                # {"display_text": "CDT", "id": "CDT"},
                {"display_text": "PST", "id": "PST"},
            ],
        }
    )
    context_queue.add_to_queue(context)
    # return Menu(display, encoder_pins=(19, 18, 20), led_pin=15, id="time_menu")
    return TimeZoneConfig(
        display=display,
        rtc=rtc,
        encoder_pins=(19, 18, 20),
        led_pin=15,
    )


def start_radio_menu(display):
    context = context_queue.dequeue()
    context.router_context["next_ui_id"] = "radio_menu"
    context.ui_context.update(
        {
            "header": "Radio Menu",
            "selectables": [
                {"display_text": "Volume", "id": "set_volume"},
                {
                    "display_text": "Set Frequency",
                    "id": "set_frequency",
                },  # Added new selectable
            ],
        }
    )
    context_queue.add_to_queue(context)
    return Menu(display, encoder_pins=(19, 18, 20), led_pin=15, id="radio_menu")


def start_frequency_config(display, radio_control):
    current_context = context_queue.dequeue()
    context = Context(
        router_context={"next_ui_id": "frequency_fractional"},
        ui_context={
            "header": "integer_part",
            "min": 88,
            "max": 108,  # Range for FM frequency settings
        },
    )
    context_queue.add_to_queue(context)

    return FrequencyConfig(
        display=display,
        radio_control=radio_control,
        encoder_pins=(19, 18, 20),
        led_pin=15,
        id="set_frequency",
    )


def start_frequency_fractional_config(display, radio_control):
    current_context = context_queue.dequeue()
    context = Context(
        router_context={"next_ui_id": "main_menu"},
        ui_context={
            "header": "fractional_part",
            "min": 0,
            "max": 9,  # Range for the fractional part of the frequency
        },
    )
    context_queue.add_to_queue(context)

    return FrequencyConfig(
        display=display,
        radio_control=radio_control,
        encoder_pins=(19, 18, 20),
        led_pin=15,
        id="set_frequency_fractional",
    )


def start_main_menu(display):
    context = context_queue.dequeue()
    # Check if router_context exists
    if context is None:
        context = Context(router_context={}, ui_context={})

    context.router_context["next_ui_id"] = "main_menu"
    context.ui_context.update(
        {
            "header": "Main Menu",
            "selectables": [
                {"display_text": "Date", "id": "date_menu"},
                {"display_text": "Time", "id": "time_menu"},
                {"display_text": "Radio", "id": "radio_menu"},
            ],
        }
    )
    context_queue.add_to_queue(context)
    return Menu(display, encoder_pins=(19, 18, 20), led_pin=15, id="main_menu")


def start_set_time(display, rtc):
    context = context_queue.dequeue()
    context.router_context["next_ui_id"] = ""  # "set_hour"
    context.ui_context.update({"header": "hour", "min": 0, "max": 23})
    context_queue.add_to_queue(context)
    return start_time_config(display, rtc)


def start_time_config(display, rtc):
    return TimeConfig(
        display=display,
        rtc=rtc,
        encoder_pins=(19, 18, 20),
        led_pin=15,
    )


def start_set_date(display, rtc):
    context = context_queue.dequeue()
    context.router_context["next_ui_id"] = ""
    context.ui_context.update(
        {
            "header": "year",
            "min": 2024,
            "max": 2040,
        }
    )
    context_queue.add_to_queue(context)
    return start_date_config(display, rtc)


def start_date_config(display, rtc):
    return DateConfig(
        display=display, rtc=rtc, encoder_pins=(19, 18, 20), led_pin=15, id="set_date"
    )


menu_map = {
    "new_date": start_set_date,
    "new_time": start_set_time,
    "set_date": start_date_config,
    "set_time": start_time_config,
    "set_alarm": start_alarm_config,
    "new_alarm": start_create_alarm,
    "alarm_menu": start_alarm_menu,
    "list_alarms": start_list_alarms,
    "date_menu": start_date_menu,
    "time_menu": start_time_menu,
    "radio_menu": start_radio_menu,
    "set_volume": start_volume_config,
    "main_menu": start_main_menu,
    "set_time_mode": start_time_mode_config,
    "set_timezone": start_timezone_config,
    "alarm_disable": start_alarm_disable_config,
    "delete_alarm": start_delete_alarm_config,
    "snooze": start_snooze_config,
    "set_frequency": start_frequency_config,
    "frequency_fractional": start_frequency_fractional_config,
}


auxiliary_menu_map = {
    "radio_power": start_volume_config,
    "start_main_menu": start_main_menu,
    "stop_monitoring": None,  # Special case, handled separately
    "alarm_disable": start_alarm_disable_config,
    "snooze": start_snooze_config,
}
