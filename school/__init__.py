import sys
import os
from subprocess import call
from datetime import timedelta, datetime, date
from typing import *
from functools import partial
import argparse
import csv
import yaml

from school.config import *
from school.private_config import *

from school.course import Course, Courses
from school.utilities import *


# catch SIGINT and prevent it from terminating the script, since an instance of Ranger
# might be running and it crashes when called using subprocess.Popen (might be related
# to https://github.com/ranger/ranger/issues/898)
from signal import signal, SIGINT

signal(SIGINT, lambda _, __: None)


### GLOBAL VARIABLES ###
# change path to current folder for the script to work
# remember it, though, since we might need it
cwd = os.getcwd()
os.chdir(os.path.dirname(os.path.realpath(__file__)))


### ARGUMENTS ###
parser = argparse.ArgumentParser(
    description="A script for simplifying my university education.",
)

parser.add_argument(
    "actions",
    nargs="+",
    help="the actions for the script to make; see README for details",
)

parser.add_argument(
    "-s", "--short", dest="short", action="store_true", help="shorten the output",
)

arguments = parser.parse_args()


def list_finals(courses: Courses):
    """Lists dates of all finals."""
    # get courses that have finals records in them
    finals_courses = [c for c in courses.get_sorted_courses() if c.finals is not None]

    if len(finals_courses) == 0:
        sys.exit("No finals added yet!")

    # build a table
    finals = [["Finals!"]]

    for course in sorted(finals_courses, key=lambda c: c.finals.date):
        final = course.finals

        delta = final.date.replace(tzinfo=None) - datetime.today()
        due_msg = "done" if delta.days < 0 else f"{delta.days + 1} days"

        finals.append(
            [
                course.abbreviation if arguments.short else course.name,
                final.date.strftime("%_d. %-m. %Y"),
                final.date.strftime("%_H:%M"),
                due_msg,
                str(final.classroom.number),
            ]
        )

    print_table(finals)


def list_timeline(courses: Courses):
    """List the courses in a timeline."""
    beginning_minutes = int(7.34 * 60)  # starting time is 7:20
    end_minutes = int(21 * 60)

    interval = 100  # 100 minutes for each period (90 + 10)

    total_minutes = ((end_minutes - beginning_minutes) // interval + 1) * interval
    number_of_intervals = total_minutes // interval

    # separate courses based on weekdays
    days = [[] for _ in range(5)]
    for course in courses.get_sorted_courses(include_unscheduled=False):
        days[course.weekday()].append(course)

    # print the header
    print(
        ("╭" + "─" * (total_minutes // 10) + "╮\n│")
        + "".join(
            Ansi.bold(
                minutes_to_HHMM(beginning_minutes + interval * i).strip().ljust(10, " ")
            )
            for i in range(number_of_intervals)
        )
        + "│\n├─"
        + "".join(
            "─" * (number_of_intervals) + ("─" if i != number_of_intervals - 1 else "┤")
            for i in range(number_of_intervals)
        )
    )

    # a buffer for adding course line strings
    print_buffer = ["" for _ in range(len(days))]
    for i, day in enumerate(days):
        print_buffer[i] += "│"

        for j, course in enumerate(day):
            prev_course = days[i][j - 1]

            # duration before course start
            if j == 0:
                wait = (course.time.start - beginning_minutes) // 10
            else:
                wait = (course.time.start - prev_course.time.end) // 10

            duration = (course.time.end - course.time.start) // 10

            # python's .center aligns right and it looks ugly
            name = Ansi.color(
                (course.abbreviation).upper(), course_types[course.type][0]
            )

            if Ansi.len(name) % 2 == 0:
                name += " "

            print_buffer[i] += " " * wait + "{" + Ansi.center(name, duration - 2) + "}"

            # last course padding after
            if j == len(day) - 1:
                print_buffer[i] += " " * (
                    (beginning_minutes + total_minutes - course.time.end) // 10
                )

        print_buffer[i] += "│"

    # add current position, overriding whatever there was in the buffer
    now = datetime.now()

    weekday = now.weekday()
    offset = (now.hour * 60 + now.minute - beginning_minutes) // 10 + 1

    # print the buffer
    for line in print_buffer:
        print(line)

    # print the very last line
    print(
        "╰─"
        + "".join(
            "─" * (number_of_intervals) + ("─" if i != number_of_intervals - 1 else "╯")
            for i in range(number_of_intervals)
        )
    )


def list_courses(courses: Courses, option=""):
    """Lists information about the courses."""
    courses = courses.get_sorted_courses()

    current_day = datetime.today()
    current_weekday = current_day.weekday()

    # split to scheduled and non-scheduled
    unscheduled = [c for c in courses if c.time is None]
    courses = [c for c in courses if c not in unscheduled]

    table = []
    for i, course in enumerate(courses):
        # lambda functions to test for various options
        # a is current weekday and b is the course's weekday
        options = {
            "": lambda a, b: True,  # all of them
            "t": lambda a, b: a == b,  # today
            "tm": lambda a, b: (a + 1) % 7 == b,  # tomorrow
            "mo": lambda a, b: b == 0,
            "tu": lambda a, b: b == 1,
            "we": lambda a, b: b == 2,
            "th": lambda a, b: b == 3,
            "fr": lambda a, b: b == 4,
            "sa": lambda a, b: b == 5,
            "su": lambda a, b: b == 6,
        }

        if option not in options:
            sys.exit("Invalid option!")

        if options[option](current_weekday, course.weekday()):
            # include the name of the day before first day's course
            if courses[i - 1].time.day != courses[i].time.day:
                weekday = courses[i].time.day.capitalize()

                # calculate the next occurrence
                date = (
                    current_day
                    + timedelta(days=(course.weekday() - current_weekday) % 7)
                ).strftime("%-d. %-m.")

                table.append([f"{weekday} / {date}"])

            # for possibly surrounding the name with chars if it's ongoing
            name_surround_char = "•" if course.is_ongoing() else ""

            row = [
                f"{name_surround_char}{course.name if not arguments.short else course.abbreviation}{name_surround_char}",
                f"{minutes_to_HHMM(courses[i].time.start)} -"
                f" {minutes_to_HHMM(courses[i].time.end)}"
                + ("" if course.time.weeks is None else f" ({course.time.weeks})"),
                "-" if course.classroom is None else course.classroom.number,
            ]

            row[0] = Ansi.color(row[0], course_types[course.type][0])

            # append useful information
            table.append(row)

    # list unscheduled courses only when no options are specified
    if option == "" and len(unscheduled) != 0:
        table.append(["Nerozvrženo"])
        for course in unscheduled:
            table.append(
                [
                    course.name if not arguments.short else course.abbreviation,
                    course.type[0],
                    "-",
                    "-",
                ]
            )

    # if no courses were added since the days didn't match, exit with a message
    if len(table) == 0:
        sys.exit("No courses matching the criteria found!")

    print_table(table)


def send_mail(courses: Courses, file_name: str):
    """Send an email to the email associated with the course."""
    course = Course.from_path(os.path.dirname(os.path.join(cwd, file_name)))

    if course is None:
        sys.exit("Current working directory is not in a course directory.")

    if course.teacher is None:
        sys.exit("The course has no teacher to send the email to.")

    if course.teacher.email is None:
        sys.exit("The course teacher has no email address.")

    import smtplib, ssl
    from email.mime.multipart import MIMEMultipart
    from email.mime.application import MIMEApplication
    from email.mime.text import MIMEText

    print("Reading the configuration file...")
    configuration = {}
    latest_attribute = None

    config_path = os.path.join(cwd, file_name)

    for i, line in enumerate(open(config_path)):
        # tabs are multi-line attributes
        if line.startswith("\t"):
            if latest_attribute is None:
                sys.exit(f"Expected attribute before tab:\n{i}: {line}")
            configuration[latest_attribute] += line.strip() + "\n"
            continue

        # skip empty lines
        if len(line.strip()) == 0:
            continue

        if ":" not in line:
            sys.exit(f"Malformed line (missing ':'):\n{i}: {line}")

        attribute, value = (
            line[: line.find(":")].strip().lower(),
            line[line.find(":") + 1 :].strip(),
        )

        configuration[attribute] = value
        latest_attribute = attribute

    print("Composing the message...")
    message = MIMEMultipart()
    message["From"] = smtp_from
    message["To"] = course.teacher.email

    for required in {"subject", "body", "attachments"}:
        if required not in configuration:
            sys.exit(f"{required.capitalize()} not read!")

    message["Subject"] = configuration["subject"]
    message.attach(MIMEText(configuration["body"]))

    for attachment in map(lambda x: x.strip(), configuration["attachments"].split()):
        extension = attachment.split(".")[-1]
        attachment_path = os.path.join(os.path.dirname(config_path), attachment)

        if not os.path.exists(attachment_path):
            sys.exit(f"Attachment '{attachment}' missing!")

        att = MIMEApplication(open(attachment_path, "rb").read())
        att.add_header("content-disposition", "attachment", filename=attachment)
        message.attach(att)

    print(f"Sending mail to '{course.teacher.email}'.")
    while (answer := input("Yes/no: ")) :
        if answer == "yes":
            break
        else:
            sys.exit("Aborting.")

    print("Connecting to the SMPT server...")
    try:
        smtp_server = smtplib.SMTP_SSL(smtp_address, smtp_port)
        smtp_server.login(smtp_login, smtp_password)
        smtp_server.send_message(message)
    except Exception as e:
        exit(f"Something went wrong when connecting to the SMTP server: {e}")

    smtp_server.close()


def open_course(kind: str, courses: Courses, argument: Optional[str] = None):
    """Open the course's something."""
    # if no argument is specified, default to getting the current or the next course
    courses = courses.get_course_from_argument(argument)

    # if none were found
    if len(courses) == 0:
        sys.exit(f"No course matching the criteria.")

    # if one was found
    elif len(courses) == 1:
        course = courses[0]

        if kind == "website":
            if course.website is not None:
                open_web_browser(course.website)
            else:
                sys.exit("The course has no website.")

        elif kind == "folder":
            open_file_browser(course.path())

        elif kind == "notes":
            path = os.path.join(course.path(), "notes.xopp")

            # check if the default notes exist
            if not os.path.isfile(path):
                sys.exit(f"The course has no notes.")
            else:
                open_in_xournalpp(path)

    # if multiple were found
    else:
        # if multiple courses were found and they're all the same, open course folder
        if kind == "folder" and all(
            [
                courses[i].abbreviation == courses[i + 1].abbreviation
                for i in range(len(courses) - 1)
            ]
        ):
            open_file_browser(courses[0].path(ignore_type=True))

        # if multiple courses were found and the websites match, open it
        elif kind == "website" and all(
            [
                courses[i].website == courses[i + 1].website
                for i in range(len(courses) - 1)
            ]
        ):
            open_web_browser(courses[0].website)

        else:
            sys.exit(f"Multiple courses matching the identifier.")


def get_cron_schedule(minutes: int, day: int) -> str:
    """Returns the cron schedule expression for the specified parameters."""
    return f"{minutes % 60} {minutes // 60} * * {day + 1}"  # day + 1, since 0 == Sunday


def get_next_course_message(i: int, courses: list) -> str:
    """Returns the string of the cron job that should be ran for the upcoming course."""
    course = (
        None
        if i + 1 >= len(courses) or courses[i].time.day != courses[i + 1].time.day
        else courses[i + 1]
    )

    return (
        notify_no_more_courses
        if course is None
        else notify_next_course_message.format(
            course.name,
            course.type,
            course.time.start - courses[i].time.end,
            "?" if course.classroom is None else course.classroom.number,
        )
    )


def compile_cron_jobs(courses: Courses):
    """Adds notifications for upcoming classes to the crontab file."""
    # check if the script is running as root; if not, call itself as root
    if not os.geteuid() == 0:
        call(["sudo", "-E", *sys.argv])
        sys.exit()

    courses = courses.get_sorted_courses(include_unscheduled=False)

    cron_file = "/etc/crontab"
    user = os.getlogin()

    # comments to encapsulate the generated cron jobs
    cron_file_comments = {
        "beginning": (
            "# BEGINNING: course schedule crons (autogenerated, do not change)"
        ),
        "end": "# END: course schedule crons",
    }

    # if it doesn't exist, create it
    if not os.path.exists(cron_file):
        open(cron_file, "w")

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

                i += 1
                break
            else:
                f.write(contents[i])

            i += 1

        f.write(cron_file_comments["beginning"] + "\n")

        for j, course in enumerate(courses):
            # the messages regarding the course
            messages = [
                (
                    get_cron_schedule(course.time.end - 5, course.weekday()),
                    get_next_course_message(j, courses),
                ),
                (
                    get_cron_schedule(course.time.start, course.weekday()),
                    f"{notify_started_message} <i>{course.name} ({course.type})</i>.",
                ),
            ]

            for cron_schedule, body in messages:
                f.write(f"{cron_schedule} {user} {notify_command} '{body}'\n")

        f.write(cron_file_comments["end"] + "\n")

        # write the rest of the file
        while i < len(contents):
            f.write(contents[i])
            i += 1

        # cut whatever is left
        f.truncate()

        print(f"Course messages generated and saved to {cron_file}.")


def initialize(courses: Courses, option=""):
    """Initialize a new year from a CSV from SIS. Found in Rozvrh NG -> CSV."""
    path = os.path.join(cwd, option)

    def recursive_dictionary_clear(d):
        """Recursively clear dictionary keys with empty values."""
        for key in list(d):
            if type(d[key]) == dict:
                recursive_dictionary_clear(d[key])

            if d[key] == "" or d[key] == {}:
                del d[key]

    if option == "":
        sys.exit("ERROR: No CSV specified.")

    if not os.path.exists(path):
        sys.exit("ERROR: Specified file doesn't exist.")

    with open(path, "rb") as f:
        contents = f.read().decode("cp1250")

        for l in list(csv.reader(contents.splitlines(), delimiter=";"))[1:]:
            uid, _, code, name, day, start, cls, dur, _, _, _, weeks, teacher = l

            out = {
                "teacher": {"name": teacher},
                "classroom": cls,
                "time": {
                    "day": WD_EN[int(day) - 1].capitalize(),
                    "start": int(start),  # TODO HH:MM formatting
                    "end": int(start) + int(dur),  # TODO HH:MM formatting
                    "weeks": "even"
                    if weeks == "sude"
                    else "odd"
                    if weeks == "liche"
                    else "",
                },
                "code": code
            }

            recursive_dictionary_clear(out)

            # create a basic abbreviation
            abbreviation = "".join(
                [
                    word[0].upper() if word[0].isalpha() or word[0].isdigit() else ""
                    for word in name.split()
                ]
            )

            # create the directory with the name of the course
            course_dir = os.path.join(cwd, f"{name} ({abbreviation})")
            if not os.path.exists(course_dir):
                os.mkdir(course_dir)

            # lecture / lab
            course_type = "přednáška" if uid[:-1].endswith("p") else "cvičení"

            if not os.path.exists(os.path.join(course_dir, course_type)):
                os.mkdir(os.path.join(course_dir, course_type))

            with open(os.path.join(course_dir, course_type, "info.yaml"), "w") as f:
                yaml.dump(out, stream=f, allow_unicode=True)


if __name__ == "__main__":
    action_tree = {
        ("list",): {
            ("courses",): list_courses,
            ("finals",): list_finals,
            ("timeline",): list_timeline,
        },
        ("cron",): compile_cron_jobs,
        ("send",): send_mail,
        ("open",): {
            ("course",): partial(open_course, "folder"),
            ("website",): partial(open_course, "website"),
            ("notes",): partial(open_course, "notes"),
        },
        ("initialize",): initialize,
    }


# go down the action tree
    while len(arguments.actions) != 0 and type(action_tree) is dict:
        action = arguments.actions.pop(0)

        # sort the actions by their common prefix with the argument
        actions = sorted(
            (max([len(action) if s.startswith(action) else 0 for s in d]), d)
            for d in action_tree
        )

        # if no match is found, quit with error
        if actions[-1][0] == 0:
            sys.exit(
                f"ERROR: '{action}' doesn't match actions in the action tree:"
                f" {{{', '.join(' or '.join(d) for d in action_tree)}}}"
            )

        # filter out the sub-optimal actions
        actions = list(filter(lambda x: x[0] == actions[-1][0], actions))

        # if there are multiple optimal solutions, the command is ambiguous
        if len(actions) > 1:
            sys.exit(
                f"ERROR: Ambiguous actions for '{action}':"
                f" {{{', '.join(' or '.join(d) for _, d in actions)}}}",
            )
        else:
            action_tree = action_tree[actions[0][1]]

# if the action tree isn't a function by now, exit; else extract the function
    if type(action_tree) is dict:
        sys.exit(
            "ERROR: Actions remaining:"
            f" {{{', '.join(' or '.join(d) for d in action_tree)}}}"
        )

    try:
        action_tree(Courses(), *arguments.actions)
    except TypeError:
        print("ERROR: Invalid arguments for the specified action.")
