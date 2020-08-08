from typing import *
from datetime import datetime, date
from dataclasses import *
from yaml import safe_load, YAMLError
from urllib.request import urlopen
from unidecode import unidecode
import sys
import os

from config import *
from private_config import *

from utilities import *


@dataclass
class Strict:
    """A class for strictly checking whether each of the dataclass variable types match."""

    def __post_init__(self):
        """Perform the check."""
        for name, field_type in self.__annotations__.items():
            value = self.__dict__[name]

            # ignore None values and Any types
            if value is None or field_type is Any:
                continue

            # go through all of the field types and check the types
            for f in (
                get_args(field_type)
                if get_origin(field_type) is Union
                else [field_type]
            ):
                if isinstance(value, f):
                    break
            else:
                raise TypeError(
                    f"The key '{name}' "
                    + f"in class {self.__class__.__name__} "
                    + f"expected '{field_type.__name__}' "
                    + f"but got '{type(value).__name__}' instead."
                )


@dataclass
class Teacher(Strict):
    name: Union[str, list]
    email: Union[str, list] = None
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
    name: str
    type: str
    abbreviation: str

    teacher: Teacher = None
    time: Time = None
    classroom: Classroom = None

    website: str = None
    finals: Finals = None

    other: Any = None

    def is_ongoing(self) -> bool:
        """Returns True if the course is ongoing and False if not."""
        today = datetime.today()

        return (
            False
            if self.time is not None
            else (
                today.weekday() == self.weekday()
                and self.time.start <= today.hour * 60 + today.minute <= self.time.end
            )
        )

    def weekday(self) -> int:
        """Get the weekday the course is on (counting from 0)."""
        return weekday_en_index(self.time.day.lower())

    def path(self, ignore_type: bool = False) -> str:
        """Returns the path of the course (possibly ignoring the type)."""
        return os.path.join(
            *(
                [courses_folder, f"{self.name} ({self.abbreviation})"]
                + ([] if ignore_type else [self.type])
            )
        )

    @classmethod
    def from_dictionary(cls, d: Dict):
        """Initialize a Course object from the given dictionary."""
        return cls.__from_dictionary(cls, d)

    @classmethod
    def __from_dictionary(cls, c, d):
        """A helper function that converts a nested dictionary to a dataclass.
        Inspired by https://stackoverflow.com/a/54769644."""
        if is_dataclass(c):
            fieldtypes = {f.name: f.type for f in fields(c)}
            return c(**{f: cls.__from_dictionary(fieldtypes[f], d[f]) for f in d})
        else:
            return d

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
        with open(path, "r") as f:
            try:
                # descend 2 levels down, getting the name of the course directory
                # not pretty, but functional
                root = path
                for _ in range(3):
                    root = os.path.dirname(root)
                shortened_path = path[len(root) + 1 :]

                name = shortened_path[: shortened_path.index(os.sep)]
                abbreviation = name[name.rfind(" ") :][1:]

                if not abbreviation.startswith("(") or not abbreviation.endswith(")"):
                    raise ValueError(
                        f"The course abbreviation '{abbreviation}' in '{name}' is not"
                        " valid."
                    )

                abbreviation = abbreviation[1:-1]

                shortened_path = shortened_path[len(name) + 1 :]
                course_type = shortened_path[: shortened_path.index(os.sep)]

                if course_type not in course_types:
                    raise ValueError(
                        f"The course type '{course_type}' in '{name}' is not valid."
                    )

                course_dict = safe_load(f) or {}
                course_dict["name"] = name[: name.rfind(" ")]
                course_dict["type"] = course_type
                course_dict["abbreviation"] = abbreviation

                return Course.from_dictionary(course_dict)
            except (YAMLError, TypeError) as e:
                sys.exit(f"ERROR in {path}: {e}")
            except KeyError as e:
                sys.exit(f"ERROR in {path}: Invalid key {e}.")


class Courses:
    """A class for working with all of the courses."""

    def __init__(self):
        self.courses: List[Courses] = []

        for root, _, filenames in os.walk(courses_folder):
            for filename in filter(lambda f: f.endswith(".yaml"), filenames):
                self.courses.append(Course.from_file(os.path.join(root, filename)))

    def get_sorted_courses(self, include_unscheduled=False) -> List[Course]:
        """Return the courses, sorted by when they start during the week."""
        return sorted(
            filter(lambda c: c.time is not None or include_unscheduled, self.courses),
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
        if argument is None:
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

            return [min_course]

        # try to interpret the argument as an abbreviation
        if "-" not in argument:
            abbr = argument
            type = None
        else:
            # split on the first -
            abbr, type = argument.split("-", 1)

        # courses that were parsed as if the argument before - was an abbreviation
        abbr_courses = [
            course
            for course in self.get_sorted_courses()
            if abbr == course.abbreviation.lower() and type in (None, course.type[0])
        ]

        # courses that were parsed as if the argument before - was a name
        name_courses = [
            course
            for course in self.get_sorted_courses()
            if unidecode(course.name.lower()).startswith(unidecode(abbr.lower()))
            and type in {None, course.type[0]}
        ]

        # return the courses for argument as an abbreviation or for argument as a name
        return abbr_courses if len(abbr_courses) != 0 else name_courses
