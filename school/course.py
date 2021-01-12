import csv
import os
from datetime import date, datetime, timedelta
from re import match, split
from subprocess import call, Popen, DEVNULL

import yaml
from unidecode import unidecode

from utilities import *


@dataclass
class Teacher(Strict):
    name: Union[str, List[str]]
    email: Union[str, List[str]] = None
    website: str = None
    office: str = None
    note: str = None


@dataclass
class Classroom(Strict):
    address: str = None
    number: str = None
    floor: int = None


@dataclass
class Time(Strict):
    day: str
    start: int
    end: int
    weeks: str = None


@dataclass
class Finals(Strict):
    date: date
    classroom: Classroom


@dataclass
class Course(Strict):
    # these three are not in the YAML itself, but instead added from the path to it
    # -----------------------------------------------------------------------------
    # name: str
    # type: str
    # abbreviation: str
    # folder: str

    code: str = None

    teacher: Teacher = None
    time: Time = None
    classroom: Classroom = None

    website: Union[str, List[str]] = None
    online: str = None
    finals: Finals = None

    # links to resources that are to be periodically updated with 'course update'
    # either ["filename", "url"] or
    # either [["thing to match in hrefs of all urls 1", "thing...", ...], "url"]
    resources: List[List[Union[str, List[str]]]] = None

    def is_ongoing(self) -> bool:
        """Returns True if the course is ongoing and False if not."""
        today = datetime.today()

        return (
            False
            if self.time is None
            else (
                today.weekday() == self.weekday()
                and self.time.start <= today.hour * 60 + today.minute <= self.time.end
            )
        )

    def weekday(self) -> int:
        """Get the weekday the course is on (counting from 0)."""
        return WD_EN.index(self.time.day.lower())

    def path(self, ignore_type: bool = False) -> str:
        """Returns the path of the course (possibly ignoring the type)."""
        return os.path.join(
            *(
                [self.folder, f"{self.name} ({self.abbreviation})"]
                + ([] if ignore_type else [self.type])
            )
        )

    @classmethod
    def from_path(cls, path: str):
        """Initialize a Course object from anywhere within its path."""
        # go down until we find it
        while path != os.path.dirname(path):
            for f in os.listdir(path):
                if f.endswith(".yaml"):
                    return Course.from_file(os.path.join(path, f))
            else:
                path = os.path.dirname(path)

        return None

    @classmethod
    def from_file(cls, path: str):
        """Initialize a Course object from the path to its .yaml dictionary."""
        # descend 2 levels down, getting the name of the course directory
        # not pretty, but functional
        root = path
        for _ in range(3):
            root = os.path.dirname(root)
        shortened_path = path[len(root) + 1 :]

        name = shortened_path[: shortened_path.index(os.sep)]
        abbreviation = name[name.rfind(" ") :][1:]

        invalid_abbreviation_error = (
            f"The course abbreviation '{abbreviation}' in '{name}' is not valid."
        )

        # abbreviation not surrounded by brackets
        if not abbreviation.startswith("(") or not abbreviation.endswith(")"):
            exit_with_error(invalid_abbreviation_error)

        abbreviation = abbreviation[1:-1]

        # empty abbreviation
        if len(abbreviation.strip()) == 0:
            exit_with_error(invalid_abbreviation_error)

        shortened_path = shortened_path[len(name) + 1 :]
        course_type = shortened_path[: shortened_path.index(os.sep)]

        if course_type not in course_types:
            sys.exit(f"The course type '{course_type}' in '{name}' is not valid.")

        course = Course._from_file(path)

        course.name = name[: name.rfind(" ")]
        course.type = course_type
        course.abbreviation = abbreviation
        course.folder = root

        return course


class Courses:
    """A class for working with all of the courses."""

    def __init__(self, folder: str):
        """Create a Courses object from a given string."""
        self.folder = folder

    def get_courses(self) -> List[Course]:
        """Get all of the courses in no particular order."""
        courses: List[Course] = []

        for root, dirs, filenames in os.walk(self.folder):
            # https://stackoverflow.com/questions/13454164/os-walk-without-hidden-folders
            # ---
            # CAREFUL: dirs[:] is necessary, since it overwrites the contents, not just
            # the reference
            filenames = [f for f in filenames if not f[0] == "."]
            dirs[:] = [d for d in dirs if not d[0] == "."]

            for filename in filter(lambda f: f == "info.yaml", filenames):
                courses.append(Course.from_file(os.path.join(root, filename)))

        return courses

    def get_sorted_courses(self, include_unscheduled=False) -> List[Course]:
        """Return the courses, sorted by when they start during the week."""
        return sorted(
            filter(
                lambda c: c.time is not None or include_unscheduled, self.get_courses()
            ),
            key=lambda c: (0, 0) if not c.time else (c.weekday(), c.time.start),
        )

    def get_ongoing_course(self) -> Optional[Course]:
        """Returns the currently ongoing course (or None if there is none)."""
        for course in self.get_sorted_courses():
            if course.is_ongoing():
                return course

    def get_course_from_argument(self, argument: str) -> List[Course]:
        """Returns all courses that match the format name-[type] or abbreviation-[type]."""
        # if no argument is specified, get the ongoing/next course
        if argument == "":
            ongoing = self.get_ongoing_course()
            return (
                [ongoing]
                if ongoing is not None
                else self.get_course_from_argument("next")
            )

        argument = argument.lower().strip()

        # special case for 'next'
        if argument in ("n", "next"):
            today = datetime.today()

            MID = 1440  # minutes in a day
            MIW = 10080  # minutes in a week

            current_week_time = today.weekday() * MID + today.hour * 60 + today.minute
            min_time, min_course = float("+inf"), None

            # find the course starting the soonest from now
            for course in self.get_sorted_courses(include_unscheduled=False):
                time_to_course = (
                    (course.time.start + course.weekday() * MID) - current_week_time
                ) % MIW

                if time_to_course < min_time:
                    min_time = time_to_course
                    min_course = course

            return [min_course] if min_course is not None else []

        # try to interpret the argument as an abbreviation
        if "-" not in argument:
            c_abbr = argument
            c_type = None
        else:
            # split on the first -
            c_abbr, c_type = argument.split("-", 1)

        # courses that were parsed as if the argument before - was an abbreviation
        abbr_courses = [
            course
            for course in self.get_sorted_courses(include_unscheduled=True)
            if c_abbr == course.abbreviation.lower()
            and c_type in (None, course.type[0])
        ]

        # courses that were parsed as if the argument before - was a name
        name_courses = [
            course
            for course in self.get_sorted_courses()
            if unidecode(course.name.lower()).startswith(unidecode(c_abbr.lower()))
            and c_type in {None, course.type[0]}
        ]

        # return the courses for argument as an abbreviation or for argument as a name
        return abbr_courses if len(abbr_courses) != 0 else name_courses

    def list(self, option: str = "", short=False, **kwargs):
        """Lists information about the courses."""
        courses = self.get_sorted_courses()

        if option == "plain":
            for course in sorted(courses, key=lambda x: x.abbreviation + x.type):
                print(f"{course.abbreviation}-{course.type[0]}")
            quit()

        current_day = datetime.today()
        current_weekday = current_day.weekday()

        # split to scheduled and non-scheduled
        unscheduled = [c for c in courses if c.time is None]
        courses = [c for c in courses if c not in unscheduled]

        table = []
        option = option.lower()

        for i, course in enumerate(courses):
            # lambda functions to test for various options
            # a is current weekday and b is the course's weekday
            options = {
                "": lambda _, __: True,  # all of them
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
                exit_with_error("Invalid course-listing option!")

            if options[option](current_weekday, course.weekday()):
                # include the name of the day before first day's course
                if courses[i - 1].time.day != courses[i].time.day:
                    weekday = course.time.day.capitalize()

                    # calculate the next occurrence
                    date = (
                        current_day
                        + timedelta(days=(course.weekday() - current_weekday) % 7)
                    ).strftime("%-d. %-m.")

                    table.append([f"{weekday if not short else weekday[:3]} / {date}"])

                # for possibly surrounding the name with chars if it's ongoing
                name_surround_char = "•" if course.is_ongoing() else ""

                row = [
                    f"{name_surround_char}{course.name if not short else course.abbreviation}{name_surround_char}",
                    f"{minutes_to_HHMM(course.time.start)} -"
                    f" {minutes_to_HHMM(course.time.end)}"
                    + (
                        ""
                        if course.time.weeks is None
                        else (
                            f" ({course.time.weeks if not short else course.time.weeks[0]})"
                        )
                    ),
                    "-" if course.classroom is None else course.classroom.number,
                ]

                # color the course name the appropriate color, depending on its type
                row[0] = Ansi.color(row[0], course_types[course.type].color)

                # append useful information
                table.append(row)

        # list unscheduled courses only when no options are specified
        if option == "" and len(unscheduled) != 0:
            table.append(["Unscheduled"])
            for course in unscheduled:
                table.append(
                    [
                        course.name if not short else course.abbreviation,
                        course.type[0],
                        "-",
                        "-",
                    ]
                )

        if len(table) == 0:
            exit_with_error("No courses matching the criteria found!")

        print_table(table)

    def finals(self, short=False, **kwargs):
        """Lists dates of all finals."""
        # get courses that have finals records in them
        finals_courses = [c for c in self.get_sorted_courses(include_unscheduled=True) if c.finals is not None]

        if len(finals_courses) == 0:
            print("No finals added yet!")
            sys.exit(0)

        # build a table
        finals = [["Finals!"]]

        for course in sorted(finals_courses, key=lambda c: c.finals.date):
            final = course.finals

            # get the due message

            delta = final.date.replace() - datetime.now()
            due_msg = due_message_from_timedelta(delta)
            if delta.days < 0:
                due_msg = "done"

            finals.append(
                [
                    Ansi.color(
                        course.abbreviation if short else course.name,
                        course_types[course.type].color,
                    ),
                    final.date.strftime("%_d. %-m. %Y"),
                    final.date.strftime("%_H:%M"),
                    due_msg,
                    str(final.classroom.number),
                ]
            )

        print_table(finals)

    def compile_cron_jobs(self, **kwargs):
        """Adds notifications for upcoming classes to the crontab file."""

        def get_cron_schedule(minutes: int, day: int) -> str:
            """Returns the cron schedule expression for the specified parameters."""
            return (  # day + 1, since 0 == Sunday
                f"{minutes % 60} {minutes // 60} * * {day + 1}"
            )

        def get_next_course_message(i: int, courses: list) -> str:
            """Returns the string of the cron job that should be ran for the upcoming course."""
            course = (
                None
                if i + 1 >= len(courses)
                or courses[i].time.day != courses[i + 1].time.day
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

        # check if the script is running as root; if not, call itself as root
        if not os.geteuid() == 0:
            call(["sudo", "-E", *sys.argv])
            sys.exit()

        courses = self.get_sorted_courses(include_unscheduled=False)

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
                        f"{notify_started_message} <i>{course.name}"
                        f" ({course.type})</i>.",
                    ),
                ]

                for cron_schedule, body in messages:
                    f.write(f"{cron_schedule} {user}{hack} {notify_command} '{body}'\n")

            f.write(cron_file_comments["end"] + "\n")

            # write the rest of the file
            while i < len(contents):
                f.write(contents[i])
                i += 1

            # cut whatever is left
            f.truncate()

            print(f"Course messages generated and saved to {cron_file}.")

    def timeline(self, **kwargs):
        """List the courses in a timeline."""

        def rtm(n, multiple=10):
            """Round to multiple."""
            return int(multiple * round(float(n) / multiple))

        beginning_minutes = 7 * 60 + 20  # starting time is 7:20
        end_minutes = 21 * 60  # ending time is 21:00

        interval = 100  # 100 minutes for each period (90 + 10)

        total_minutes = ((end_minutes - beginning_minutes) // interval + 1) * interval
        number_of_intervals = total_minutes // interval

        # separate courses based on weekdays
        days = [[] for _ in range(7)]
        for course in self.get_sorted_courses(include_unscheduled=False):
            days[course.weekday()].append(course)

        # print the header
        print(
            ("     ╭" + "─" * (total_minutes // 10) + "╮\n     │")
            + "".join(
                Ansi.bold(
                    minutes_to_HHMM(beginning_minutes + interval * i)
                    .strip()
                    .ljust(10, " ")
                )
                for i in range(number_of_intervals)
            )
            + "│\n╭────┼─"
            + "".join(
                "─" * number_of_intervals
                + ("─" if i != number_of_intervals - 1 else "┤")
                for i in range(number_of_intervals)
            )
        )

        # a buffer for adding course line strings
        print_buffer = ["" for _ in range(len(days))]
        for i, day in enumerate(days):
            print_buffer[i] += f"│ {WD_EN[i][:2].capitalize()} │"

            for j, course in enumerate(day):
                prev_course = days[i][j - 1]

                # duration before course start
                if j == 0:
                    wait = (rtm(course.time.start) - beginning_minutes) // 10
                else:
                    wait = (rtm(course.time.start) - rtm(prev_course.time.end)) // 10

                # the space between { and }
                space = (rtm(course.time.end) - rtm(course.time.start)) // 10 - 2

                name = Ansi.color(
                    course.abbreviation
                    if len(course.abbreviation) <= (space)
                    else course.abbreviation[: space - 1] + ".",
                    course_types[course.type].color,
                )

                # python's .center aligns right and it looks ugly
                if Ansi.len(name) % 2 == 0 and Ansi.len(name) != space:
                    name += " "

                print_buffer[i] += " " * wait + "{" + Ansi.center(name, space) + "}"

                # last course padding after
                if j == len(day) - 1:
                    course_padding = (
                        beginning_minutes + total_minutes - rtm(course.time.end)
                    ) // 10
                    break
            else:
                course_padding = total_minutes // 10

            print_buffer[i] += " " * course_padding + "│"

        # print the buffer
        for line in print_buffer:
            print(line)

        # print the very last line
        print(
            "╰────┴─"
            + "".join(
                "─" * number_of_intervals
                + ("─" if i != number_of_intervals - 1 else "╯")
                for i in range(number_of_intervals)
            )
        )

    def open(self, kind: str, option: str = "", **kwargs):
        """Open the course's something."""

        def open_file_browser(path: str):
            """Opens the specified path in a file browser."""
            call(file_browser + [path])

        def open_web_browser(url: str):
            """Opens the specified website in a web browser."""
            Popen(web_browser + [url], stdout=DEVNULL, stderr=DEVNULL)

        def open_in_text_editor(path: str):
            """Opens the specified website in a web browser."""
            call(text_editor + [path])

        def open_in_note_app(app: str, path: str):
            """Opens the specified file in its associated note app."""
            call([app, path])

        # if no argument is specified, default to getting the current or the next course
        courses = self.get_course_from_argument(option)

        if len(courses) == 0:
            exit_with_error("No course matching the criteria.")

        elif len(courses) == 1:
            course = courses[0]

            if kind == "website":
                if course.website is None:
                    exit_with_error("The course has no website.")
                elif isinstance(course.website, list):
                    website = pick_one(course.website)
                else:
                    website = course.website

                open_web_browser(website)

            elif kind == "folder":
                open_file_browser(course.path())

            elif kind == "notes":
                files = [f for f in os.listdir(course.path()) if f.startswith("notes")]

                if len(files) == 0:
                    exit_with_error("The course has no notes.")

                f = pick_one(files)

                for ext in note_handlers:
                    if f.endswith(ext):
                        open_in_note_app(
                            note_handlers[ext], os.path.join(course.path(), f)
                        )
                        break
                else:
                    exit_with_error("The note type has no associated handler.")

            elif kind == "online":
                if course.online is not None:
                    open_web_browser(course.online)
                else:
                    exit_with_error("The course has no online link.")

        else:
            # if multiple courses were found and they're all the same (but different
            # type), open the general course folder
            if kind == "folder" and all(
                [
                    courses[i].abbreviation == courses[i + 1].abbreviation
                    for i in range(len(courses) - 1)
                ]
            ):
                open_file_browser(courses[0].path(ignore_type=True))
            else:
                exit_with_error("Multiple courses matching.")

    def initialize(self, cwd: str, option: str = "", **kwargs):
        """Initialize a new year from a CSV from SIS (found in Rozvrh NG -> CSV)."""
        # TODO: make the times when the courses start prettier
        path = os.path.join(cwd, option)

        def recursive_dictionary_clear(d):
            """Recursively clear dictionary keys with empty values."""
            for key in list(d):
                if isinstance(d[key], dict):
                    recursive_dictionary_clear(d[key])

                if d[key] == "" or d[key] == {}:
                    del d[key]

        def format_teacher(teacher):
            """An ungly, hard-coded way to format the names of the teachers. Couldn't
            find something more solid, so this will have to do for now."""
            l = split(
                "|".join(
                    [
                        "doc\.",
                        "Ing\.",
                        "Ph.D\.",
                        "CSc\.",
                        "PhDr\.",
                        "DrSc\.",
                        "Mgr\.",
                        "RNDr\.",
                        "M\.Sc\.",
                        "Bc\.",
                        "Dr\.",
                        "D\.Phil\.",
                        "Ph\.",
                        "r\.",
                    ]
                ),
                teacher,
            )
            l = [i.strip().strip(",").strip() for i in l]
            l = [i for i in l if i not in (",", "")]
            return " / ".join([" ".join(list(reversed(i.split()))) for i in l])

        if option == "":
            exit_with_error("No CSV to initialize from specified.")

        if not os.path.exists(path):
            exit_with_error("Specified file doesn't exist.")

        with open(path, "rb") as f:
            # SIS uses cp1250 :(
            contents = f.read().decode("cp1250")

            course_count = 0
            for l in list(csv.reader(contents.splitlines(), delimiter=";"))[1:]:
                uid, _, code, name, day, start, self, dur, _, _, _, weeks, teacher = l

                teacher = format_teacher(teacher)

                # ATTENTION: watch out for 'and's here
                # in order for the code not to crash, they do the following:
                #          '' and x -> ''
                # 'something' and x -> x
                out = {
                    "teacher": {"name": teacher},
                    "classroom": {"number": self},
                    "time": {
                        "day": day and WD_EN[int(day) - 1].capitalize(),
                        "start": start and int(start),  # TODO HH:MM formatting
                        "end": start and int(start) + int(dur),  # TODO HH:MM formatting
                        "weeks": "even"
                        if weeks == "sude"
                        else "odd"
                        if weeks == "liche"
                        else "",
                    },
                    "code": code,
                }

                # don't print empty dictionary parts
                recursive_dictionary_clear(out)

                # create a basic abbreviation from taking first letters of each word
                abbreviation = "".join(
                    [
                        word[0].upper()
                        if word[0].isalpha() or word[0].isdigit()
                        else ""
                        for word in name.split()
                    ]
                )

                # create the directory with the name of the course
                course_dir = os.path.join(cwd, f"{name} ({abbreviation})")
                if not os.path.exists(course_dir):
                    os.mkdir(course_dir)

                # lecture / lab
                # based on the ID of the SIS ticket - labs end with x** and lectures with p*
                course_type = "přednáška" if uid[:-1].endswith("p") else "cvičení"

                if not os.path.exists(os.path.join(course_dir, course_type)):
                    os.mkdir(os.path.join(course_dir, course_type))

                with open(os.path.join(course_dir, course_type, "info.yaml"), "w") as f:
                    yaml.dump(out, stream=f, allow_unicode=True)

                course_count += 1

        exit_with_success(f"New semester with {course_count} courses initialized.")

    def resources(self, option: str = "", **kwargs):
        """Update the resources of a given course."""
        courses = (
            self.get_course_from_argument(option)
            if option != ""
            else self.get_sorted_courses(include_unscheduled=True)
        )

        def try_download(handler, url, folder, name, prefix):
            """Attempt to download the resource. Throw an exception if unsuccessful."""
            print(
                f"{prefix} saving '{name}' from '{url}'... ", end="", flush=True,
            )

            try:
                if not os.path.exists(folder):
                    os.mkdir(folder)

                handler(url, os.path.join(folder, name))
                print("success!")
            except Exception as e:
                print(f"failed with '{e}'.")

        if len(courses) == 0:
            exit_with_error("No course matching the criteria.")

        for course in courses:
            urls = course.resources
            handler = download_file
            prefix = f"[{course.abbreviation}-{course.type[0]}]"

            # skip courses without resources/videos
            if urls is None:
                continue

            folder = os.path.join(course.path(), "resources")

            for name, url in urls:
                if check_type(name, List[str]):
                    for u in get_website_links(url):
                        for n in name:
                            if match(n, u):
                                if not u.startswith("http"):
                                    if not url.endswith("/"):
                                        url = url[: -len(url.split("/")[-1])]
                                    elif u.startswith("/"):
                                        # TODO
                                        pass

                                    u = url + u

                                proper_name = u.split("/")[-1]

                                try_download(handler, u, folder, proper_name, prefix)
                else:
                    try_download(handler, url, folder, name, prefix)
