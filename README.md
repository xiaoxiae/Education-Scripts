# Lecture Notes Scripts
This repository contains scripts to simplify note-taking for CS-related courses and lectures.

## school
The main script of the repository. Performs many school-related tasks, like opening the course folder/website, printing the calendar, listing finals...

### Folder structure
The script requires a particular folder structure to function properly. By default, a `courses` folder (or a symlink) should be placed in the `school` folder of this repository, with the following contents:
```
courses
├── Course 1 (abbreviation)
│   ├── cvičení
│   │   ├── info.yaml
│   │   └── course 1 lab files...
│   └── přednáška
│       ├── info.yaml
│       └── course 1 lecture files...
├── Course 2 (abbreviation)
│   ├── cvičení
│   │   ├── info.yaml
│   │   └── course 2 lab files...
│   └── přednáška
│       ├── info.yaml
│       └── course 2 lecture files...
└── courses...
```

The courses should all be in one folder, their folder names being the course name, followed by the course abbreviation (`Algorithms I (ALG)`, for example). In each of the course folders, at least one of the folders specified in `school/config.py > course_types` should be present -- these are defined by the user and separate the given course lab/lecture/... files. In the example, "cvičení" and "přednáška" is used, since I'm Czech (they translate to "lab" and "lecture"), but feel free to use whatever you wish.

The `info.yaml` file contains all of the necessary information about the course, such as time, place, email, etc... Here is an example (see `school/course.py` for the full syntax). Here is an example:
```
teacher:
    name: John Smith
    email: smith@email.com

classroom:
    number: S11
    floor: 3

website: https://www.google.com

time:
    day: Wednesday
    start: 14:00
    end: 15:30
```

### Actions
The script supports various actions. For example, by writing `school open course alg`, you open the course with name/abbreviation `alg`. However, since this would be quite a chore to write, you can simplify by only writing the starting letters of the actions that you want to perform (`school o c alg`, in our case).

Here are the currently supported actions (the details of each are explained in the sections below):
```
school
├── list
│   ├── courses <when>
│   ├── finals
│   └── timeline
├── cron
├── send <mail file>
└── open
    ├── course <course name/abbreviation>
    ├── website <course name/abbreviation>
    └── notes <course name/abbreviation>
```

#### `list courses`
Lists all of the courses. The `<when>` can be either empty (listing all courses), `t`/`tm` (today/tomorrow) or `mo`/`tu`/`we`/`th`/`fr`/`sa`/`su` for listing courses on a given weekday.
```
╭───────────────────────◀ Pondělí / 29. 6. ▶──────────────────────╮
│ Doporučené postupy v programování │ 10:40 - 12:10        │ SU2  │
│ Lineární algebra 2                │ 14:00 - 15:30        │ S10  │
│ Doporučené postupy v programování │ 15:40 - 17:10        │ S9   │
│                                                                 │
├────────────────────────◀ Úterý / 30. 6. ▶───────────────────────┤
│ Medvědovo seminář z ADS           │  9:00 - 10:30        │ S322 │
│ Algoritmy a Datové Struktury      │ 10:40 - 12:10        │ S3   │
│ Lineární algebra 2                │ 14:00 - 15:30        │ S5   │
│ Počítačové systémy                │ 15:40 - 17:10        │ S3   │
│                                                                 │
├────────────────────────◀ Středa / 1. 7. ▶───────────────────────┤
│ Programování 2                    │  9:00 - 10:30        │ S5   │
│ The C Programming Language        │ 10:40 - 12:10        │ SU2  │
│ Počítačové systémy                │ 12:20 - 13:50 (even) │ SW2  │
│ Algoritmy a Datové Struktury      │ 14:00 - 15:30        │ S11  │
│ Úvod do Linuxu                    │ 15:40 - 17:10 (even) │ S5   │
│                                                                 │
├───────────────────────◀ Čtvrtek / 2. 7. ▶───────────────────────┤
│ Architektura počítačů             │  9:00 - 10:30        │ S5   │
│ Matematická analýza 1             │ 12:20 - 13:50        │ S1   │
│ Matematická analýza 1             │ 14:00 - 15:30        │ S3   │
│ Programování 2                    │ 15:40 - 17:10        │ S8   │
│ Úvod do řešení problémů           │ 19:20 - 21:00        │ S3   │
│                                                                 │
├────────────────────────◀ Pátek / 3. 7. ▶────────────────────────┤
│ Úvod do Linuxu                    │ 10:40 - 12:10        │ SU2  │
╰─────────────────────────────────────────────────────────────────╯
```

#### `list finals`
Lists finals for all courses. To add a final, one must add the `final` attribute to `info.yaml`:
```
╭───────────────────────────◀ Finals! ▶────────────────────────────╮
│ Algoritmy a Datové Struktury │  4. 6. 2020 │  9:30 │ done │ S3   │
│ Matematická analýza 1        │  9. 6. 2020 │ 10:00 │ done │ S5   │
│ Programování 2               │ 10. 6. 2020 │  9:00 │ done │ S3   │
│ Lineární algebra 2           │ 15. 6. 2020 │  9:00 │ done │ S9   │
│ Architektura počítačů        │ 18. 6. 2020 │ 13:00 │ done │ Zoom │
│ Počítačové systémy           │ 26. 6. 2020 │ 10:00 │ done │ Zoom │
╰──────────────────────────────────────────────────────────────────╯
```

#### `list timeline`
Lists the courses as a timeline.
```
╭──────────────────────────────────────────────────────────────────────────────────────────╮
│7:20      9:00      10:40     12:20     14:00     15:40     17:20     19:00     20:40     │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│                    {  DPP  }           {  LA   } {  DPP  }                               │
│          { ADS++ } {  ADS  }           {  LA   } {  PS   }                               │
│          { PROG  } {   C   } {  PS   } {  ADS  } { LINUX }                               │
│          {  AP   }           {  MA   } {  MA   } { PROG  }             {   IPS  }        │
│                    { LINUX }                                                             │
╰──────────────────────────────────────────────────────────────────────────────────────────╯
```

#### `cron` (experimental)
Adds an autogenerated section to `/etc/crontab` that contains notifications before the start and end of each of the classes.

#### `send` (experimental)
Generates and sends a mail from a specified format to the email from the course config (added to automate homework sending). The syntax is as follows:
```
Subject: [MA 1] řešení úkolu 4

Body:
	Ahoj,
	
	posílam řešení 4. domácího úkolu na MA 1.
	
	T. Sláma

Attachments:
	4.pdf
```

#### `open course`
Open the course with the specified name/abbreviation in the file browser specified in the script configuration. Leaving the option empty opens the upcoming course. One can also add ... TODO -p -c

#### `open website`
Open the website of the course with the specified name/abbreviation in the file browser specified in the script configuration. Leaving the option empty opens the website of the next course.

#### `open notes`
Open the `notes.xopp` file in the given course's directory in Xournal++.

### Dependencies
- [Xournal++](https://github.com/xournalpp/xournalpp)
- [Ranger](https://wiki.archlinux.org/index.php/Ranger)
- [Firefox](https://www.mozilla.org/firefox/)
- [unidecode](https://pypi.org/project/Unidecode/) and [pyyaml](https://pyyaml.org/wiki/PyYAMLDocumentation) (also specified in `requirements.txt`)


## md_to_pdf
Converts markdown files with embedded Xournal++ files to PDF (using Pandoc). Helpful when doing homework where sketches are required.

### Dependencies
- [Inkscape](https://inkscape.org/)
- [Pandoc](https://pandoc.org/)
- [Xournal++](https://github.com/xournalpp/xournalpp)
