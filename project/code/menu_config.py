# menu_config.py

from menu import Menu
from time_config import TimeConfig
from time_mode import TimeMode


def get_list_from_range(low, high):
    return [str(i) for i in range(low, high)]


# Configuration functions
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


def start_hour_config(display, rtc):
    return TimeConfig(
        display=display,
        rtc=rtc,
        encoder_pins=(19, 18, 20),
        led_pin=15,
        header="Hour",
        next_config={"id": "set_minute", "display_text": "Set Minutes"},
        min=1,
        max=23  # dynamically set based on mode
    )


def start_minute_config(display, rtc):
    return TimeConfig(
        display=display,
        rtc=rtc,
        encoder_pins=(19, 18, 20),
        led_pin=15,
        header="Minute",
        next_config={"id": "set_second", "display_text": "Set Seconds"},
        min=0,
        max=60
    )


def start_second_config(display, rtc):
    return TimeConfig(
        display=display,
        rtc=rtc,
        encoder_pins=(19, 18, 20),
        led_pin=15,
        header="Second",
        next_config={"id": "main_menu", "display_text": "Main Menu"},
        min=0,
        max=60
    )


def start_alarm_config(display):
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
    "set_minute": start_minute_config,
    "set_second": start_second_config,
    "set_alarm": start_alarm_config,
    "time_menu": start_time_menu,
    "radio_menu": start_radio_menu,
    "main_menu": start_main_menu,
    "set_time_mode": start_time_mode_config
}
