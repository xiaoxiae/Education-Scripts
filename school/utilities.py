"""A class that contains various useful utility methods."""

from subprocess import call, Popen, DEVNULL
from re import sub, compile
from typing import *

from config import *
from private_config import *


WD_EN: Final[List[str]] = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)


def weekday_en_index(day: str) -> int:
    """Return the index of the day in a week."""
    return WD_EN.index(day)


def minutes_to_HHMM(minutes: int) -> str:
    """Converts a number of minutes to a string in the form HH:MM."""
    return f"{str(minutes // 60).rjust(2)}:{minutes % 60:02d}"


def open_file_browser(path: str):
    """Opens the specified path in a file browser."""
    call(file_browser + [path])


def open_web_browser(url: str):
    """Opens the specified website in a web browser."""
    call(web_browser + [url])


def open_in_xournalpp(path: str):
    """Opens the specified Xournal++ file in Xournal++."""
    # suppress the warnings, since Xournal++ talks way too much
    Popen(["xournalpp", path], stdout=DEVNULL, stderr=DEVNULL)


class Ansi:
    """A set of ANSI convenience methods."""

    @classmethod
    def color(cls, text, color: int):
        return f"\u001b[38;5;{color}m{text}\u001b[0m"

    @classmethod
    def gray(cls, text):
        """Gray coloring."""
        return f"\u001b[38;5;240m{text}\u001b[0m"

    @classmethod
    def bold(cls, text):
        return f"\u001b[1m{text}\u001b[0m"

    @classmethod
    def underline(cls, text):
        return f"\u001b[4m{text}\u001b[0m"

    @classmethod
    def italics(cls, text):
        return f"\u001b[3m{text}\u001b[0m"

    @classmethod
    def escape(cls, text):
        return compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])").sub("", text)

    @classmethod
    def __align(cls, text: str, length: int, function: str, *args, **kwargs):
        return getattr(text, function)(
            length + (len(text) - cls.len(text)), *args, **kwargs
        )

    @classmethod
    def ljust(cls, text: str, length: int, *args, **kwargs) -> str:
        return cls.__align(text, length, "ljust", *args, **kwargs)

    @classmethod
    def rjust(cls, text: str, length: int, *args, **kwargs) -> str:
        return cls.__align(text, length, "rjust", *args, **kwargs)

    @classmethod
    def center(cls, text: str, length: int, *args, **kwargs) -> str:
        return cls.__align(text, length, "center", *args, **kwargs)

    @classmethod
    def len(cls, text: str, *args, **kwargs) -> int:
        return len(cls.escape(text))


def print_table(table: List[List[str]]):
    # find max width of each of the columns of the table
    column_widths = [0] * max(len(row) for row in table)
    for row in table:
        # skip weekday rows
        if len(row) != 1:
            for i, entry in enumerate(row):
                if column_widths[i] < Ansi.len(entry):
                    column_widths[i] = Ansi.len(entry)

    for i, row in enumerate(table):
        print(end="╭─" if i == 0 else "│ ")

        column_sep = Ansi.gray(" │ ")
        max_row_width = sum(column_widths) + Ansi.len(column_sep) * (
            len(column_widths) - 1
        )

        # if only one item is in the row, it will be printed specially
        if len(row) == 1:
            print(
                (f"{' ' * max_row_width} │\n├─" if i != 0 else "")
                + Ansi.center(Ansi.bold(f"◀ {row[0]} ▶"), max_row_width, "─")
                + ("─╮" if i == 0 else "─┤")
            )
        else:
            for j, entry in enumerate(row):
                print(
                    Ansi.ljust(entry, column_widths[j])
                    + (column_sep if j != (len(row) - 1) else " │\n"),
                    end="",
                )

    print(f"╰{'─' * (max_row_width + 2)}╯")
