import sys
import os
from yaml import safe_load, YAMLError
from subprocess import call
from datetime import timedelta, datetime
from signal import signal, SIGINT
from typing import Union


# global variables
courses_folder = "aktuální semestr/"


def get_cron_schedule(time: int, day: int) -> str:
    """Returns the cron schedule expression for the specified parameters."""
    return f"{time % 60} {time // 60} * * {day + 1}"  # day + 1, since 0 == Sunday


def get_ongoing_course() -> Union[dict, None]:
    """Returns the currently ongoing course (or None)."""
    today = datetime.today()
    weekday, current_time = today.weekday(), today.hour * 60 + today.minute

    for course in get_sorted_courses():
        course_weekday = day_index(course["time"]["day"])
        course_start, course_end = course["time"]["start"], course["time"]["end"]

        if weekday == course_weekday and course_start <= current_time <= course_end:
            return course
    else:
        return None


def get_course_from_argument(argument: str) -> list:
    """Returns all courses that match the format name-[type] or abbreviation-[type]."""
    courses = []

    parts = argument.split("-")
    course_identifier = parts[0].lower()
    course_type = None if len(parts) == 1 else parts[1].lower()

    for course in get_sorted_courses():
        name, abbr = course["name"].lower(), course["abbreviation"].lower()

        name_matches = course_identifier == name or course_identifier == abbr
        type_matches = course_type == None or course_type == course["type"][0]

        if name_matches and type_matches:
            courses.append(course)

    return courses


def get_course_path(course: dict, ignore_type: bool = False):
    """Returns the path of the specified course."""
    if ignore_type:
        return os.path.join(courses_folder, course["name"])
    else:
        return os.path.join(courses_folder, course["name"], course["type"])


def open_in_ranger(path: str) -> None:
    """Opens the specified path in Ranger."""
    call(["ranger", path])


def open_in_firefox(url: str):
    """Opens the specified website in FireFox."""
    call(["firefox", "-new-window", url])


def get_next_course_message(i: int, courses: list) -> str:
    """Returns the string of the cron job that should be ran for the upcoming course."""
    next_course = (
        None
        if i + 1 >= len(courses)
        or courses[i]["time"]["day"] != courses[i + 1]["time"]["day"]
        else courses[i + 1]
    )

    return (
        "dnes již žádný další předmět není."
        if next_course is None
        else (
            f"další předmět je <i>{next_course['name']} ({next_course['type']})</i>, "
            + f"který začíná <i>{next_course['time']['start'] - courses[i]['time']['end']} minut</i> po tomto "
            + f"v učebně <i>{next_course['classroom']['number']}</i> "
            + f"({next_course['classroom']['floor']}. patro)."
        )
    )


def minutes_to_HHMM(minutes: int) -> str:
    """Converts a number of minutes to a string in the form HH:MM."""
    return f"{str(minutes // 60).rjust(2)}:{minutes % 60:02d}"


def weekday_to_cz(day: str) -> str:
    """Converts a day in English to a day in Czech"""
    return {
        "monday": "pondělí",
        "tuesday": "úterý",
        "wednesday": "středa",
        "thursday": "čtvrtek",
        "friday": "pátek",
        "saturday": "sobota",
        "sunday": "neděle",
    }[day.lower()]


def day_index(day: str) -> int:
    """Returns the index of the day in a week."""
    return [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    ].index(day.lower())


def get_sorted_courses(sort=False) -> list:
    """Returns a list of dictionaries with the parsed courses."""
    courses = []

    for root, _, filenames in os.walk(courses_folder):
        for filename in filenames:
            if filename.endswith(".yaml"):
                with open(os.path.join(root, filename), "r") as f:
                    try:
                        courses.append(safe_load(f))
                    except YAMLError as e:
                        print(f"ERROR: {e}")
                        sys.exit()

    return sorted(
        courses, key=lambda c: (day_index(c["time"]["day"]), c["time"]["start"])
    )


def list_homework() -> None:
    """Lists information about a course's homework."""
    output = []
    for course in filter(lambda c: "homework" in c, get_sorted_courses()):
        output.append(f"{course['name']} ({course['type']}):")

        for homework in sorted(course["homework"], key=lambda x: tuple(x)):
            # not sure how to make this part better, but this is definitely not it
            date, desc = tuple(*homework.items())
            today = datetime.today().date()

            output.append(
                f"- due in {(date - today).days} days: {desc} ({date:%d/%m/%Y})"
            )

        output.append("")

    print("\n".join(output[:-1]))


def list_courses(option="") -> None:
    """Lists information about the courses."""
    courses = get_sorted_courses(sort=True)

    current_day = datetime.today()
    current_weekday = current_day.weekday()

    table = []
    for i, course in enumerate(courses):
        course_weekday = day_index(course["time"]["day"])

        if (
            (option == "t" and current_weekday == course_weekday)
            or (option == "tm" and (current_weekday + 1) % 7 == course_weekday)
            or option == ""
        ):
            # include the name of the day before first day's course
            if courses[i - 1]["time"]["day"] != courses[i]["time"]["day"]:
                # calculate the date of the next occurrence of this weekday
                weekday_date = current_day + timedelta(
                    days=(course_weekday - current_weekday) % 7
                )

                table.append(
                    [
                        f"{weekday_to_cz(courses[i]['time']['day']).capitalize()} / {weekday_date.strftime('%e. %m.')}"
                    ]
                )

            # append useful information
            table.append(
                [
                    course["name"],
                    course.get("type", "-")[0],
                    f"{minutes_to_HHMM(courses[i]['time']['start'])}-{minutes_to_HHMM(courses[i]['time']['end'])}",
                    course["classroom"].get("number", "-"),
                    str(course["classroom"].get("floor", "-")),
                ]
            )

    # if no courses were added since the days didn't match, exit with a message
    if len(table) == 0:
        print("No courses matching the criteria found!")
        sys.exit()

    # find max width of each of the columns of the table
    column_widths = [0] * max(len(row) for row in table)
    for row in table:
        # skip weekday rows
        if len(row) != 1:
            for i, entry in enumerate(row):
                if column_widths[i] < len(entry):
                    column_widths[i] = len(entry)

    for i, row in enumerate(table):
        print(end="╭─" if i == 0 else "│ ")

        column_sep = " │ "
        max_row_width = sum(column_widths) + len(column_sep) * (len(column_widths) - 1)

        # if only one item is in the row, it's the weekday and is printed specially
        if len(row) == 1:
            print(
                (f"{' ' * max_row_width} │\n├─" if i != 0 else "")
                + f"◀ {row[0]} ▶".center(max_row_width, "─")
                + ("─╮" if i == 0 else "─┤")
            )
        else:
            for j, entry in enumerate(row):
                print(
                    entry.ljust(column_widths[j])
                    + (column_sep if j != (len(row) - 1) else " │\n"),
                    end="",
                )

    print(f"╰{'─' * (max_row_width + 2)}╯")


def open_course(argument: str = None) -> None:
    """Opens the specified course in Ranger, or the current one."""
    if argument == None:
        current_course = get_ongoing_course()

        if current_course != None:
            open_in_ranger(get_course_path(current_course))
        else:
            print(f"No currently ongoing course.")
    else:
        courses = get_course_from_argument(argument)

        if len(courses) == 0:
            print(f"Course with the identifier '{argument}' not found.")
        elif len(courses) == 1:
            open_in_ranger(get_course_path(courses[0]))
        else:
            open_in_ranger(get_course_path(courses[0], ignore_type=True))


def open_website(argument: str = None) -> None:
    """Opens the specified course's website in FireFox."""
    if argument == None:
        current_course = get_ongoing_course()

        if current_course != None:
            if "website" in current_course:
                open_in_firefox(current_course["website"])
            else:
                print("The course has no website.")
        else:
            print(f"No currently ongoing course.")
    else:
        courses = get_course_from_argument(argument)

        if len(courses) == 0:
            print(f"Course with the identifier '{argument}' not found.")
        elif len(courses) == 1:
            if "website" in courses[0]:
                open_in_firefox(courses[0]["website"])
            else:
                print("The course has no website.")
        else:
            print(f"Multiple courses matching the '{argument}' identifier.")


def compile_notes() -> None:
    """Runs md_to_pdf script on all of the courses."""
    base = os.path.dirname(os.path.realpath(__file__))

    for path in map(get_course_path, get_sorted_courses()):
        os.chdir(os.path.join(base, path))
        call(["fish", "-c", "md_to_pdf -a -t"])


def compile_cron_jobs() -> None:
    """Adds notifications for upcoming classes to crontab file."""
    courses = get_sorted_courses()

    cron_file = "/etc/crontab"
    user = os.getlogin()

    # comments to encapsulate the generated cron jobs
    cron_file_comments = {
        "beginning": "# BEGINNING: course schedule crons (autogenerated, do not change)",
        "end": "# END: course schedule crons",
    }

    with open(cron_file, "r+") as f:
        contents = f.readlines()
        f.seek(0)

        # write to file till we reach the end or the comment section is skipped, so we
        # can add the new course-related cron jobs
        i = 0
        while i < len(contents):
            if contents[i].strip() == cron_file_comments["beginning"]:
                while contents[i].strip() != cron_file_comments["end"]:
                    i += 1
                else:
                    i += 1
                    break
            else:
                f.write(contents[i])

            i += 1

        f.write(cron_file_comments["beginning"] + "\n")

        for j, course in enumerate(courses):
            day = day_index(course["time"]["day"])

            # the messages regarding the course
            messages = [
                (
                    get_cron_schedule(course["time"]["end"] - 5, day),
                    get_next_course_message(j, courses),
                ),
                (
                    get_cron_schedule(course["time"]["start"], day),
                    f"právě začal předmět <i>{course['name']} ({course['type']})</i>.",
                ),
            ]

            for cron_schedule, body in messages:
                f.write(f"{cron_schedule} {user} dunstify rozvrh '{body}'\n")

        f.write(cron_file_comments["end"] + "\n")

        # write the rest of the file
        while i < len(contents):
            f.write(contents[i])
            i += 1

        f.truncate()


def list_recursive_help(tree: dict, indentation: int) -> None:
    """Recursively pretty-prints a nested dictionary (with lists being functions)."""
    for decision in tree:
        if type(tree[decision]) != dict:
            print(
                ("  " * indentation + "{" + decision + "}").ljust(20)
                + tree[decision].__doc__
            )
        else:
            print("  " * indentation + f"{{{decision}}}")
            list_recursive_help(tree[decision], indentation + 1)


# catch SIGINT and prevent it from terminating the script, since an instance of Ranger
# might be running and it crashes when called using subprocess. Popen (might be related
# to https://github.com/ranger/ranger/issues/898)
signal(SIGINT, lambda _x, _y: None)

# change path to current folder for the script to work
os.chdir(os.path.dirname(os.path.realpath(__file__)))

decision_tree = {
    "list": {"courses": list_courses, "homework": list_homework},
    "compile": {"cron": compile_cron_jobs, "notes": compile_notes},
    "open": {"course": open_course, "website": open_website},
}

arguments = sys.argv[1:]

# if no arguments are specified, list help
if len(arguments) == 0:
    print(
        "A multi-purpose script for simplifying my MFF UK education.\n"
        + "\n"
        + "supported options:"
    )

    list_recursive_help(decision_tree, 1)
    sys.exit()

# go down the decision tree
while len(arguments) != 0 and type(decision_tree) is dict:
    argument = arguments.pop(0)

    # sort the decisions by their common prefix with the argument
    decisions = sorted(
        (len(argument) if argument == d[: len(argument)] else 0, d)
        for d in decision_tree
    )

    # if no match is found, quit with error
    if decisions[-1][0] == 0:
        print(
            f"ERROR: '{argument}' doesn't match decisions in the decision tree:",
            str(tuple(d for _, d in decisions)),
        )

        sys.exit()

    # filter out the sub-optimal decisions
    decisions = list(filter(lambda x: x == decisions[-1], decisions))

    # if there are multiple optimal solutions, the command is ambiguous
    if len(decisions) > 1:
        print(
            f"ERROR: Ambiguous decisions for '{argument}':",
            str(tuple(d for _, d in decisions)),
        )

        sys.exit()
    else:
        decision_tree = decision_tree[decisions[0][1]]

# if the decision tree isn't a function by now, exit
if type(decision_tree) == dict:
    print("ERROR: Decisions remaining:", str(tuple(decision_tree)))

    sys.exit()

# pass the courses folder and the rest of the arguments to the function
if len(arguments) == 0:
    decision_tree()
else:
    decision_tree(*arguments)
