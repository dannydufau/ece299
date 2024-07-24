from menu import Menu
from time_config import TimeConfig
from time_mode import TimeMode
from alarm_config import AlarmConfig
from alarm_disable import AlarmDisable
from alarm_delete import AlarmDelete
from alarm_snooze import AlarmSnooze
from context_queue import context_queue
from context import Context


def get_list_from_range(low, high):
    return [str(i) for i in range(low, high)]


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
                    {"display_text": "Radio", "id": "radio_menu"}
                ]
            }
        )
        context_queue.add_to_queue(context)
        return start_main_menu(display)
    
    # Otherwise return the snooze alarm config
    context = Context(
        router_context={"next_ui_id": "main_menu"},
        ui_context={
            "header": "Disable Snooze?",
            "min": 0,
            "max": 1,
            "snooze": True
        }
    )
    context_queue.add_to_queue(context)
    return AlarmSnooze(
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
        id="set_volume"
    )


def start_list_alarms(display, rtc):
    current_context = context_queue.dequeue()

    alarms = rtc.get_alarm_times()
    selectables = [
        {
            "display_text": f"{alarm[1]['hour']:02d}:{alarm[1]['minute']:02d}:{alarm[1]['second']:02d}",
            "id": "delete_alarm",
            "context": {"alarm_id": alarm[0]}
        }
        for alarm in alarms
    ] or [{"display_text": "No alarms set", "id": "main_menu"}]

    context = Context(
        router_context={"next_ui_id": "list_alarms"},
        ui_context={
            "header": "Alarm Delete",
            "selectables": selectables
        }
    )
    #print(f"LIST UI: {context.ui_context}")
    #print(f"LIST ROUTER: {context.router_context}")
    context_queue.add_to_queue(context)
    return Menu(display, encoder_pins=(19, 18, 20), led_pin=15, id="list_alarms")


def start_delete_alarm_config(display, rtc, alarm_id):
    return AlarmDelete(
        display=display,
        rtc=rtc,
        encoder_pins=(19, 18, 20),
        led_pin=15,
        alarm_id=alarm_id
    )


def start_alarm_config(display, rtc):
    return AlarmConfig(
        display=display,
        rtc=rtc,
        encoder_pins=(19, 18, 20),
        led_pin=15,
    )

def start_time_config(display, rtc):
    return TimeConfig(
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
    context.ui_context.update({
        "header": "hour",
        "min": 0,
        "max": 24
    })
    context_queue.add_to_queue(context)
    return start_alarm_config(display, rtc)


def start_set_time(display, rtc):
    context = context_queue.dequeue()
    context.router_context["next_ui_id"] = "set_hour"
    context.ui_context.update({
        "header": "hour",
        "min": 0,
        "max": 23
    })
    context_queue.add_to_queue(context)
    return start_time_config(display, rtc)


def start_alarm_menu(display):
    context = context_queue.dequeue()
    context.router_context["next_ui_id"] = "alarm_menu"
    context.ui_context.update({
        "header": "Alarm Menu",
        "selectables": [
            {"display_text": "New Alarm", "id": "new_alarm"},
            {"display_text": "List", "id": "list_alarms"}
        ]
    })
    context_queue.add_to_queue(context)
    return Menu(display, encoder_pins=(19, 18, 20), led_pin=15, id="alarm_menu")


def start_time_menu(display):
    context = context_queue.dequeue()
    context.router_context["next_ui_id"] = "time_menu"
    context.ui_context.update({
        "header": "Time Menu",
        "selectables": [
            {"display_text": "Set Time", "id": "new_time"},
            {"display_text": "Set Alarm", "id": "alarm_menu"},
            {"display_text": "Set Time Mode", "id": "set_time_mode"}
        ]
    })
    context_queue.add_to_queue(context)
    return Menu(display, encoder_pins=(19, 18, 20), led_pin=15, id="time_menu")


def start_time_mode_config(display, rtc):
    return TimeMode(
        display=display,
        rtc=rtc,
        encoder_pins=(19, 18, 20),
        led_pin=15,
        header="Time Mode"
    )


def start_radio_menu(display):
    context = context_queue.dequeue()
    context.router_context["next_ui_id"] = "radio_menu"
    context.ui_context.update({
        "header": "Radio Menu",
        "selectables": [
            {"display_text": "Volume", "id": "set_volume"}
        ]
    })
    context_queue.add_to_queue(context)
    return Menu(display, encoder_pins=(19, 18, 20), led_pin=15, id="radio_menu")


def start_main_menu(display):
    context = context_queue.dequeue()
    context.router_context["next_ui_id"] = "main_menu"
    context.ui_context.update({
        "header": "Main Menu",
        "selectables": [
            {"display_text": "Time", "id": "time_menu"},
            {"display_text": "Radio", "id": "radio_menu"}
        ]
    })
    context_queue.add_to_queue(context)
    return Menu(display, encoder_pins=(19, 18, 20), led_pin=15, id="main_menu")


def start_hour_config(display, rtc):
    return TimeConfig(
        display=display,
        rtc=rtc,
        encoder_pins=(19, 18, 20),
        led_pin=15,
    )


def start_minute_config(display, rtc):
    return TimeConfig(
        display=display,
        rtc=rtc,
        encoder_pins=(19, 18, 20),
        led_pin=15,
    )


def start_seconds_config(display, rtc):
    return TimeConfig(
        display=display,
        rtc=rtc,
        encoder_pins=(19, 18, 20),
        led_pin=15,
    )


menu_map = {
    "set_volume": start_volume_config,
    "new_time": start_set_time,
    "set_time": start_time_config,
    "set_alarm": start_alarm_config,
    "new_alarm": start_create_alarm,
    "alarm_menu": start_alarm_menu,
    "list_alarms": start_list_alarms,
    "time_menu": start_time_menu,
    "radio_menu": start_radio_menu,
    "main_menu": start_main_menu,
    "set_time_mode": start_time_mode_config,
    "alarm_disable": start_alarm_disable_config,
    "delete_alarm": start_delete_alarm_config,
    "snooze": start_snooze_config,
}


auxiliary_menu_map = {
    "radio_power": start_volume_config,
    "start_main_menu": start_main_menu,
    "stop_monitoring": None,  # Special case, handled separately
    "alarm_disable": start_alarm_disable_config,
    "snooze": start_snooze_config,
}
