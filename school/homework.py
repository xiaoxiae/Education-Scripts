"""A module for handling homework."""
from typing import *
from dataclasses import *
from subprocess import call
from datetime import date, datetime
from random import choice
from string import ascii_lowercase
import os

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
        """Generate a homework UID."""
        return "".join([choice(ascii_lowercase) for _ in range(3)])


class Homeworks:
    """A class for working with homeworks."""

    @classmethod
    def get_homeworks(cls, option: str = "", completed=False, undeadlined=True):
        """Get all homework( object)s, sorted by their due date. If option is specified,
        only get homework from specified courses."""
        homeworks = []

        # either get all homework, or only homework for a particular class
        courses = (
            Courses.get_sorted_courses()
            if option == ""
            else Courses.get_course_from_argument(option)
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

    @classmethod
    def list(cls, option: str = "", short: bool = False, **kwargs):
        # build a table
        table = [["Homework"]]

        homeworks = (
            cls.get_homeworks(option)
            if option != "all"
            else cls.get_homeworks(completed=True, undeadlined=True)
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

            row = [
                str(homework.uid),
                Ansi.color(
                    homework.course.abbreviation if short else homework.course.name,
                    course_types[homework.course.type][0],
                ),
                homework.name or "-",
                "-"
                if homework.deadline is None
                else homework.deadline.strftime("%_d. %-m. %Y"),
                "-"
                if homework.deadline is None
                else homework.deadline.strftime("%_H:%M"),
                due_msg,
            ]

            # don't show the date, only show in how long is it due
            if short:
                row.pop(3)
                row.pop(3)

            table.append(row)

        # if no homework is added, be happy
        if len(table) == 1:
            print("No homework found!")
            return

        print_table(table)

    @classmethod
    def edit(cls, uid: str, **kwargs):
        """Edit a homework with the specified UID."""
        for homework in cls.get_homeworks(completed=True, undeadlined=True):
            if homework.uid == uid:
                open_in_text_editor(homework.path)
                return

        exit_with_error(f"No homework with UID '{uid}' found.")

    @classmethod
    def add(cls, option: str, **kwargs):
        """Edit a homework with the specified UID."""
        courses = Courses.get_course_from_argument(option)

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
        homeworks = cls.get_homeworks(completed=True, undeadlined=True)
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

        cls.edit(uid)

    @classmethod
    def delete(cls, uid: str, **kwargs):
        """Delete a homework with the specified UID."""
        for homework in cls.get_homeworks(completed=True, undeadlined=True):
            if homework.uid == uid:
                os.remove(homework.path)
                exit_with_success(f"Homework '{uid}' deleted.")

        exit_with_error(f"No homework with UID '{uid}' found.")

    @classmethod
    def complete(cls, uid: str, **kwargs):
        """Mark a homework with the specified UID as complete. Although using sed is
        likely more prone to breakage, I don't want Pyyaml messing with my formatting,
        so it's going to stay this way."""
        for homework in cls.get_homeworks(completed=True, undeadlined=True):
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
