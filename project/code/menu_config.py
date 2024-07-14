# menu_config.py

from menu import Menu
from time_config import TimeConfig
from time_mode import TimeMode
from alarm_config import AlarmConfig


def get_list_from_range(low, high):
    return [str(i) for i in range(low, high)]


# Configuration functions
def start_alarm_disable_config(display, rtc):
    return AlarmConfig(
        display=display,
        rtc=rtc,
        encoder_pins=(19, 18, 20),
        led_pin=15,
    )

def start_volume_config(display):
    # TODO: this is broken
    return Menu(
        display=display,
        encoder_pins=(19, 18, 20),
        led_pin=15,
        header="Set the Volume",
        selectables=get_list_from_range(1, 5),
        id="set_volume"
    )


def start_hour_config(
    display,
    rtc,
    time_or_alarm="time",
    next_config={"id": "set_minute", "display_text": "Set Minutes"}
):
    return TimeConfig(
        display=display,
        rtc=rtc,
        time_or_alarm=time_or_alarm,
        encoder_pins=(19, 18, 20),
        led_pin=15,
        header="Hour",
        # TODO:::::::::::::::::::::::: need set_minute or set_minute_alarm
        next_config=next_config,
        min=1,
        max=23,  # dynamically set based on mode
    )


def start_minute_config(
    display,
    rtc,
    time_or_alarm="time",
    next_config={"id": "set_seconds", "display_text": "Set Seconds"}
):
    return TimeConfig(
        display=display,
        rtc=rtc,
        time_or_alarm=time_or_alarm,
        encoder_pins=(19, 18, 20),
        led_pin=15,
        header="Minute",
        next_config=next_config,
        min=0,
        max=59,
    )


def start_seconds_config(
    display,
    rtc,
    time_or_alarm="time",
    next_config={"id": "main_menu", "display_text": "Main Menu"}
):
    return TimeConfig(
        display=display,
        rtc=rtc,
        time_or_alarm=time_or_alarm,
        encoder_pins=(19, 18, 20),
        led_pin=15,
        header="Seconds",
        next_config=next_config,
        min=0,
        max=59,
    )


def start_alarm_config(display):
    return Menu(
        display=display,
        encoder_pins=(19, 18, 20),
        led_pin=15,
        header="Set the alarm",
        selectables=[
            {"display_text": "Hours", "id": "set_hour_alarm"},
            {"display_text": "Minutes", "id": "set_minute_alarm"},
            {"display_text": "Seconds", "id": "set_seconds_alarm"}
        ],
        id="set_alarm"
    )


def start_time_menu(display):
    return Menu(
        display=display,
        encoder_pins=(19, 18, 20),
        led_pin=15,
        header="Time Menu",
        selectables=[
            {"display_text": "set time", "id": "set_hour"},
            {"display_text": "set alarm", "id": "set_alarm"},
            {"display_text": "set time mode", "id": "set_time_mode"}
        ],
        id="time_menu"
    )


def start_time_mode_config(display, rtc):
    return TimeMode(
        display=display,
        rtc=rtc,
        encoder_pins=(19, 18, 20),
        led_pin=15,
        header="Time Mode",
        next_config={"id": "main_menu", "display_text": "Main Menu"}
    )


def start_radio_menu(display):
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


def start_main_menu(display):
    return Menu(
        display=display,
        encoder_pins=(19, 18, 20),
        led_pin=15,
        header="Main Menu",
        selectables=[
            {"display_text": "Time", "id": "time_menu"},
            {"display_text": "Radio", "id": "radio_menu"}
        ],
        id="main_menu"
    )


menu_map = {
    "set_volume": start_volume_config,
    "set_hour": start_hour_config,
    "set_hour_alarm": start_hour_config,
    "set_minute": start_minute_config,
    "set_minute_alarm": start_minute_config,
    "set_seconds": start_seconds_config,
    "set_seconds_alarm": start_seconds_config,
    "set_alarm": start_alarm_config,
    "time_menu": start_time_menu,
    "radio_menu": start_radio_menu,
    "main_menu": start_main_menu,
    "set_time_mode": start_time_mode_config,
    "alarm_disable": start_alarm_disable_config
}
