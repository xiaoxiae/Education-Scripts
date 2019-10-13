import sys
import os
import yaml
import subprocess
import datetime
import signal


def get_cron_schedule(time: int, day: int) -> str:
    """Returns the cron schedule expression for the specified parameters."""
    return f"{time % 60} {time // 60} * * {day + 1}"  # day + 1, since 0 == Sunday


def get_next_course_message(i: int, courses: list) -> str:
    """Return the string of the cron job that should be ran for the upcoming course."""
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


def prefix_length(s1: str, s2: str) -> int:
    """Return the length of the second string if it's a prefix of the first, else 0."""
    return len(s2) if s2 == s1[: len(s2)] else 0


def minutes_to_HHMM(minutes: int) -> str:
    """Convert a number of minutes to a string in the form HH:MM."""
    return f"{minutes // 60}:{minutes % 60:02d}"


def weekday_to_cz(day: str) -> str:
    """Convert a day in English to a day in Czech"""
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
    """Return the index of the day in a week."""
    return [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    ].index(day.lower())


def get_sorted_courses(path: str) -> list:
    """Return a list of dictionaries with the parsed courses."""
    courses = []

    for root, _, filenames in os.walk(path):
        for filename in filenames:
            if filename.endswith(".yaml"):
                with open(os.path.join(root, filename), "r") as f:
                    try:
                        courses.append(yaml.safe_load(f))
                    except yaml.YAMLError as e:
                        print(f"Error parsing YAML: {e}")

    return sorted(
        courses, key=lambda x: (day_index(x["time"]["day"]), x["time"]["start"])
    )


def list_homework(folder: str) -> None:
    """List information about a course's homework."""
    output = []
    for course in filter(lambda x: "homework" in x, get_sorted_courses(folder)):
        output.append(f"{course['name']} ({course['type']}):")

        for homework in sorted(course["homework"], key=lambda x: tuple(x)):
            # not sure how to make this part better, but this is definitely not it
            date, desc = tuple(*homework.items())
            today = datetime.datetime.today().date()

            output.append(
                f"- due in {(date - today).days} days: {desc} ({date:%d/%m/%Y})"
            )

        output.append("")

    print("\n".join(output[:-1]))


def list_courses(folder: str, option="") -> None:
    """List information about the courses."""
    courses = get_sorted_courses(folder)
    current_day = datetime.datetime.today().weekday()

    table = []
    for i, course in enumerate(courses):
        course_day = day_index(course["time"]["day"])

        if prefix_length("today", option) == 0 or current_day == course_day:
            # include the name of the day before first day's course
            if courses[i - 1]["time"]["day"] != courses[i]["time"]["day"]:
                next_course_day = current_day

                table.append([weekday_to_cz(courses[i]["time"]["day"]).capitalize()])

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

    # if no courses were added since the days didn't match
    if len(table) == 0:
        print("No courses today!")
        sys.exit()

    column_widths = [0] * max(len(row) for row in table)

    # find max width of each of the columns of the table
    for row in table:
        # skip weekday rows
        if len(row) != 1:
            for i, entry in enumerate(row):
                if column_widths[i] < len(entry):
                    column_widths[i] = len(entry)

    # print the columns
    for i, row in enumerate(table):
        print(end="| ")
        max_row_width = sum(column_widths) + 3 * (len(column_widths) - 1)

        # if only one item is in the row, it's the weekday
        if len(row) == 1:
            # don't skip a line when the entry is the very first one
            if i != 0:
                print(" " * max_row_width, end=" |\n| ")

            print(row[0].center(max_row_width, "_"), end=" |")
        else:
            for i, entry in enumerate(row):
                print(entry.ljust(column_widths[i]), end=" | ")
        print()

    print("| " + "-" * max_row_width, end=" |\n")


def open_course(folder: str, argument: str = None) -> None:
    """Open the specified course in Ranger."""
    if argument == None:
        current_date = datetime.datetime.today()

        current_day = current_date.weekday()
        current_minutes = current_date.hour * 60 + current_date.minute
    else:
        parts = argument.split("-")  # the argument from the command line

        course_identifier = parts[0].lower()
        course_type = None if len(parts) <= 1 else parts[1].lower()

    for course in get_sorted_courses(folder):
        # information about the current course
        name, abbr = course["name"].lower(), course["abbreviation"].lower()
        weekday, minutes = course["name"].lower(), course["abbreviation"].lower()
        path = os.path.join(folder, course["name"])

        if course_identifier == name or course_identifier == abbr:
            if course_type is None:
                subprocess.call(["ranger", path])
                break
            elif course_type == course["type"][0]:
                subprocess.call(["ranger", os.path.join(path, course["type"])])
                break

    else:
        print(f"Course with the identifier '{argument}' not found.")


def compile_notes(folder: str) -> None:
    """Run md_to_pdf script on all of the courses."""
    # recursively find all folders with an info.yaml file
    for root, _, filenames in os.walk(folder):
        for filename in filenames:
            if filename == "info.yaml":
                print(root)
                # call the md_to_pdf Python script (defined as a Fish function)
                subprocess.call(["fish", "-c", "md_to_pdf -a -t"])


def compile_cron_jobs(folder: str) -> None:
    """Add notifications for upcoming classes to crontab file."""
    courses = get_sorted_courses(folder)

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
    """Recursively pretty-print a nested dictionary (with lists being functions)."""
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
# might be running and it crashes when called using subprocess.Popen (might be related
# to https://github.com/ranger/ranger/issues/898)
signal.signal(signal.SIGINT, lambda _x, _y: None)

# change path to current folder for the script to work
os.chdir(os.path.dirname(os.path.realpath(__file__)))

courses_folder = "aktuální semestr/"
arguments = sys.argv[1:]

decision_tree = {
    "list": {"courses": list_courses, "homework": list_homework},
    "compile": {"cron": compile_cron_jobs, "notes": compile_notes},
    "open": open_course,
}

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
    decisions = sorted((prefix_length(d, argument), d) for d in decision_tree)

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
    decision_tree(courses_folder)
else:
    decision_tree(courses_folder, *arguments)
