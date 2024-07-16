from menu import Menu
from time_config import TimeConfig
from time_mode import TimeMode
from alarm_config import AlarmConfig
from alarm_disable import AlarmDisable


def get_list_from_range(low, high):
    return [str(i) for i in range(low, high)]


# Configuration functions
def start_alarm_disable_config(display, rtc):
    return AlarmDisable(
        display=display,
        rtc=rtc,
        encoder_pins=(19, 18, 20),
        led_pin=15,
    )


def start_volume_config(display):
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
    next_config={"id": "set_minute", "display_text": "Set Minutes"}
):
    return TimeConfig(
        display=display,
        rtc=rtc,
        encoder_pins=(19, 18, 20),
        led_pin=15,
        header="Hour",
        next_config=next_config,
        min=1,
        max=24,
    )


def start_minute_config(
    display,
    rtc,
    next_config={"id": "set_seconds", "display_text": "Set Seconds"}
):
    return TimeConfig(
        display=display,
        rtc=rtc,
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
    next_config={"id": "main_menu", "display_text": "Main Menu"}
):
    return TimeConfig(
        display=display,
        rtc=rtc,
        encoder_pins=(19, 18, 20),
        led_pin=15,
        header="Seconds",
        next_config=next_config,
        min=0,
        max=59,
    )


def start_alarm_hour_config(
    display,
    rtc,
    alarm_id,
    next_config={"id": "set_minute_alarm", "display_text": "Set Alarm Minutes"},
):
    print(f"hour: alarm id: {alarm_id}")
    return AlarmConfig(
        display=display,
        rtc=rtc,
        encoder_pins=(19, 18, 20),
        led_pin=15,
        header="Hour",
        next_config=next_config,
        min=1,
        max=24,
        alarm_id=alarm_id
    )


def start_alarm_minute_config(
    display,
    rtc,
    alarm_id,
    next_config={"id": "set_seconds_alarm", "display_text": "Set Alarm Seconds"},
):
    print(f"minute: alarm_id: {alarm_id}")
    return AlarmConfig(
        display=display,
        rtc=rtc,
        encoder_pins=(19, 18, 20),
        led_pin=15,
        header="Minute",
        next_config=next_config,
        min=0,
        max=59,
        alarm_id=alarm_id
    )


def start_alarm_seconds_config(
    display,
    rtc,
    alarm_id,
    next_config={"id": "main_menu", "display_text": "Main Menu"},
):
    return AlarmConfig(
        display=display,
        rtc=rtc,
        encoder_pins=(19, 18, 20),
        led_pin=15,
        header="Seconds",
        next_config=next_config,
        min=0,
        max=59,
        alarm_id=alarm_id
    )


def start_alarm_menu(display):
    return Menu(
        display=display,
        encoder_pins=(19, 18, 20),
        led_pin=15,
        header="Alarm Menu",
        selectables=[
            {"display_text": "List Alarms", "id": "list_alarms"},
            {"display_text": "Create Alarm", "id": "create_alarm"}
        ],
        id="alarm_menu"
    )


def start_list_alarms(display, rtc):
    alarms = rtc.get_alarm_times()
    selectables = [
        {"display_text": f"{alarm[1]['hour']:02d}:{alarm[1]['minute']:02d}:{alarm[1]['second']:02d}", "id": "main_menu"}
        for alarm in alarms
    ] or [{"display_text": "No alarms set", "id": "main_menu"}]
    return Menu(
        display=display,
        encoder_pins=(19, 18, 20),
        led_pin=15,
        header="List Alarms",
        selectables=selectables,
        id="list_alarms"
    )


def start_create_alarm(display, rtc):
    # Generate a new alarm ID using the new_alarm method
    # Note: we do this here so that hours_config is aware of the id on save
    new_alarm_id = rtc.new_alarm()
    # Pass the new alarm ID to the configuration
    return start_alarm_hour_config(display, rtc, alarm_id=new_alarm_id)


def start_time_menu(display):
    return Menu(
        display=display,
        encoder_pins=(19, 18, 20),
        led_pin=15,
        header="Time Menu",
        selectables=[
            {"display_text": "set time", "id": "set_hour"},
            {"display_text": "set alarm", "id": "alarm_menu"},
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
    "set_hour_alarm": start_alarm_hour_config,
    "set_minute": start_minute_config,
    "set_minute_alarm": start_alarm_minute_config,
    "set_seconds": start_seconds_config,
    "set_seconds_alarm": start_alarm_seconds_config,
    "alarm_menu": start_alarm_menu,
    "list_alarms": start_list_alarms,
    "create_alarm": start_create_alarm,
    "time_menu": start_time_menu,
    "radio_menu": start_radio_menu,
    "main_menu": start_main_menu,
    "set_time_mode": start_time_mode_config,
    "alarm_disable": start_alarm_disable_config
}
