# Lecture Notes Scripts
This repository contains scripts to simplify note-taking for CS-related courses and lectures.

## school
The main script of the repository. Perform many school-related tasks, like opening the course folder/website, printing the calendar, listing finals...

**NOTE:** The script is currently localized to Czech, since that is the language that I speak. I have plans to switch to English, so I do apologize if you're interested in using it but don't speak Czech.

### Folder structure
The script requires a particular folder structure to function properly:

```
aktuální semestr
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

The courses should all be in one folder, their folder names being the course name, followed by the course abbreviation (`Algorithms I (ALG)`, for example). In each of the course folders, at least one of the folders `cvičení` (lab) and `přednáška` (lecture) should be present (depending on whether the course has either a lecture, a lab, or both).

The `info.yaml` file contains all of the necessary information about the course, such as time, place, email, etc... Here is an example (see `school/course.py` for the full syntax).
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
The script supports various actions that you can make. For example, by writing `school open course alg`, you open the course with name/abbreviation `alg`. However, since this would be quite a chore to write, you can simplify by only writing the starting letters of the actions that you want to perform (`school o c alg`, in our case).

Here are the currently supported actions (the details of each are explained in the sections below, but note that they have colors that I can't add to a README file):
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
Lists all of the courses. The `<when>` can be either empty (listing all courses), `t/tm` (today/tomorrow) or `mo/tu/we/th/fr/sa/su` for a day of the week. Adding `--short` changes the full names to abbreviations.
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
Lists all of the finals. Adding `--short` changes the full names to abbreviations.
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
Generates and sends a mail from a specified format to the email from the course config (added to automate homework sending).
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
Open the course with the specified name/abbreviation in the file browser specified in the script configuration. Leaving the option empty opens the next course.

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
