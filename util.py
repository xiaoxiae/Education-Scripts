"""A class that contains various useful utility methods."""

from subprocess import call, Popen, DEVNULL
from urllib.request import urlopen


# weekday constants
WD_EN = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
WD_CZ = ("pondělí", "úterý", "středa", "čtvrtek", "pátek", "sobota", "neděle")


def weekday_to_cz(day: str) -> str:
    """Converts a day in English to a day in Czech"""
    return dict(list(zip(WD_EN, WD_CZ)))[day.lower()]


def weekday_to_en(day: str) -> str:
    """Converts a day in Czech to a day in English"""
    return dict(list(zip(WD_CZ, WD_EN)))[day.lower()]


def weekday_en_index(day: str) -> int:
    """Return the index of the day in a week."""
    return WD_EN.index(day)


def get_cron_schedule(time: int, day: int) -> str:
    """Returns the cron schedule expression for the specified parameters."""
    return f"{time % 60} {time // 60} * * {day + 1}"  # day + 1, since 0 == Sunday


def minutes_to_HHMM(minutes: int) -> str:
    """Converts a number of minutes to a string in the form HH:MM."""
    return f"{str(minutes // 60).rjust(2)}:{minutes % 60:02d}"


def open_in_vim(path: str):
    """Opens the specified path in Vim."""
    call(["vim", path])


def open_in_ranger(path: str):
    """Opens the specified path in Ranger."""
    call(["ranger", path])


def open_in_firefox(url: str):
    """Opens the specified website in FireFox."""
    Popen(["firefox", "-new-window", url])


def open_in_xournalpp(path: str):
    """Opens the specified Xournal++ file in Xournal++."""
    # suppress the warnings, since Xournal++ talks way too much
    Popen(["xournalpp", path], stdout=DEVNULL, stderr=DEVNULL)
