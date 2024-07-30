# timezones.py

TIMEZONE_OFFSETS = {
    "UTC": 0,
    "CST": -6, # Mexico City
    "CDT": -5, # Mexico City Daylight Time
    "PST": -8,
}

def get_timezone_offset(timezone):
    """
    Get the offset in hours for the given timezone.
    """
    return TIMEZONE_OFFSETS.get(timezone.upper(), 0)
