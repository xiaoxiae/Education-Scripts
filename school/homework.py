"""A module for handling homework."""
import os
from datetime import date, datetime
from random import choice
from string import ascii_lowercase
from subprocess import call

from course import Course, Courses
from utilities import *

HW_FOLDER = ".homework"


@dataclass
class Homework(Strict):
    # these three are not in the YAML itself, but instead from variables when created
    # -------------------------------------------------------------------------------
    # path: str
    # course: Course

    uid: str  # a course UID to identify it (for editing it)
    completed: bool

    name: str = None
    description: str = None
    deadline: Union[date, str] = None  # str for special stuff like 'next course'

    @classmethod
    def from_file(cls, path: str, course: Course):
        """Initialize a Homework object from the path to its .yaml dictionary. Must be
        created this way."""
        hw = Homework._from_file(path)

        # additional attributes that it is good for homework objects to have
        hw.path = path
        hw.course = course

        return hw

    @classmethod
    def get_uid(cls):
        """Generate a homework UID. Size 2 gives 26^2 = 676. That should be more than
        enough individual homework assignments for a semester. I hope."""
        return "".join([choice(ascii_lowercase) for _ in range(2)])


class Homeworks:
    """A class for working with homeworks."""

    def __init__(self, courses: Courses):
        self.courses = courses

    def filter_by_homework(self, courses):
        """Filter out courses that can't have homework."""
        return [c for c in courses if course_types[c.type].has_homework]

    def get_homeworks(self, option: str = "", completed=False, undeadlined=True):
        """Get all homework( object)s, sorted by their due date. If option is specified,
        only get homework from specified courses."""
        homeworks = []

        # either get all homework, or only homework for a particular class
        courses = self.filter_by_homework(
            self.courses.get_sorted_courses(include_unscheduled=True)
            if option == ""
            else self.filter_by_homework(self.courses.get_course_from_argument(option))
        )

        for course in courses:
            # they are stored in a .homework file of each course
            hw_base_path = os.path.join(course.path(), HW_FOLDER)

            if os.path.exists(hw_base_path):
                for path in os.listdir(hw_base_path):
                    hw_path = os.path.join(hw_base_path, path)

                    if os.path.isfile(hw_path):
                        hw = Homework.from_file(hw_path, course)

                        # add all, or only the completed ones if specified
                        if not hw.completed or completed:
                            homeworks.append(hw)

        return sorted(
            filter(lambda h: h.deadline is not None or undeadlined, homeworks),
            key=lambda h: h.deadline or datetime.max,
        )

    def list(self, option: str = "", short: bool = False, **kwargs):
        # build a table
        table = [["Homework"]]

        homeworks = (
            self.get_homeworks(option)
            if option != "all"
            else self.get_homeworks(completed=True, undeadlined=True)
        )

        saw_undeadlined = False
        for homework in homeworks:
            # for putting an 'undeadlined' section in the table
            if homework.deadline is None:
                if not saw_undeadlined:
                    table.append(["Without deadline"])
                    saw_undeadlined = True
                due_msg = "-"
            else:
                delta = homework.deadline.replace(tzinfo=None) - datetime.now()
                due_msg = due_message_from_timedelta(delta)

                # custom due message for overdue/completed homework
                if homework.completed:
                    due_msg = "completed"
                elif delta.days < 0:
                    due_msg = f"overdue ({due_msg})"

            # highlight names that have a description
            name_highlight = lambda x: (x if homework.description is None else Ansi.bold(x))

            row = [
                str(homework.uid),
                Ansi.color(
                    homework.course.abbreviation if short else homework.course.name,
                    course_types[homework.course.type].color,
                ),
                name_highlight(homework.name or "-"),
                due_msg,
            ]

            table.append(row)

        # if no homework is added, be happy
        if len(table) == 1:
            exit_with_error("No homework found!")

        print_table(table)

    def edit(self, uid: str, **kwargs):
        """Edit a homework with the specified UID."""

        def open_in_text_editor(path: str):
            """Opens the specified website in a web browser."""
            call(text_editor + [path])

        for homework in self.get_homeworks(completed=True, undeadlined=True):
            if homework.uid == uid:
                open_in_text_editor(homework.path)
                self.list("")
                return

        exit_with_error(f"No homework with UID '{uid}' found.")

    def add(self, option: str, **kwargs):
        """Add a new homework."""
        courses = self.filter_by_homework(self.courses.get_course_from_argument(option))

        if len(courses) == 0:
            exit_with_error("No course matching the criteria.")

        if len(courses) >= 2:
            exit_with_error("Multiple courses matching.")

        course = courses[0]

        path = course.path()
        hw_dir = os.path.join(path, HW_FOLDER)

        # create the homework folder, if it doesn't exist
        if not os.path.exists(hw_dir):
            os.mkdir(hw_dir)

        # generate a unique UID
        homeworks = self.get_homeworks(completed=True, undeadlined=True)
        while True:
            uid = Homework.get_uid()

            for homework in homeworks:
                if homework.uid == uid:
                    break
            else:
                break

        with open(os.path.join(hw_dir, f"{uid}.yaml"), "w") as f:
            now = datetime.now()
            f.write(
                f"uid: {uid}\n"
                f"name: \n"
                f"description: \n"
                f"deadline: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"\n"
                f"completed: False\n"
            )

        self.edit(uid)

    def delete(self, uid: str, **kwargs):
        """Delete a homework with the specified UID."""
        for homework in self.get_homeworks(completed=True, undeadlined=True):
            if homework.uid == uid:
                os.remove(homework.path)
                exit_with_success(f"Homework '{uid}' deleted.")

        exit_with_error(f"No homework with UID '{uid}' found.")

    def complete(self, uid: str, **kwargs):
        """Mark a homework with the specified UID as complete. Although using sed is
        likely more prone to breakage, I don't want Pyyaml messing with my formatting,
        so it's going to stay this way."""
        for homework in self.get_homeworks(completed=True, undeadlined=True):
            if homework.uid == uid:
                call(
                    [
                        "sed",
                        "-i",
                        "s/^\s*completed\s*:\s*False\s*/completed: True/",
                        homework.path,
                    ]
                )
                return

        exit_with_error(f"No homework with UID '{uid}' found.")
