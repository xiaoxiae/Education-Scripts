# Education Scripts

## `school`
The main script of the repository. Performs many school-related tasks, like opening the course folder/website, printing the calendar, listing finals, etc.

### Starting out
If you're a student of a school that uses SIS, use `school initialize <schedule CSV>` to create this structure automatically (taken from `SIS -> Rozvrh NG -> Zobrazit všechny předměty -> CSV`).
If not, see "Folder Structure" section of this document to create the structure manually.

### Actions
The script supports various actions.
For example, by writing `school open course alg`, you open the course with name/abbreviation `alg`.
However, since this would be quite a chore to write, you can simplify by only writing the starting letters of the actions that you want to perform (`school o c alg`, in our case).

Here are the currently supported actions (the details of each are explained in the sections below).
The 'or' between some of the names for the actions means that either name can be used to call it, since it's tedious to remember whether to 'remove' a homework or to 'delete' it...

```
school
├── list
│   ├── courses <when>
│   ├── finals
│   └── timeline
│
├── open
│   ├── course  <course name/abbreviation>
│   ├── website <course name/abbreviation>
│   ├── lsf     <course name/abbreviation>
│   ├── notes   <course name/abbreviation>
│   └── online  <course name/abbreviation>
│
├── initialize <schedule CSV>
│
└── homework
    ├── list                   <course name/abbreviation/'all'>
    ├── add or new             <course name/abbreviation>
    ├── edit                   <homework UID>
    ├── remove or delete       <homework UID>
    ├── complete or finish     <homework UID>
    ├── incomplete or unfinish <homework UID>
    └── extrapolate            <course name/abbreviation>
```

#### `list courses`
Lists all of the courses. The `<when>` can be either empty (listing all courses), `t`/`tm` (today/tomorrow) or `mo`/`tu`/`we`/`th`/`fr`/`sa`/`su` for listing courses on a given weekday.

```
╭───────────────────────◀ Monday / 31. 8. ▶───────────────────────╮
│ Doporučené postupy v programování │ 10:40 - 12:10        │ SU2  │
│ Lineární algebra 2                │ 14:00 - 15:30        │ S10  │
│ Doporučené postupy v programování │ 15:40 - 17:10        │ S9   │
│                                                                 │
├───────────────────────◀ Tuesday / 1. 9. ▶───────────────────────┤
│ Medvědovo seminář z ADS           │  9:00 - 10:30        │ S322 │
│ Algoritmy a Datové Struktury      │ 10:40 - 12:10        │ S3   │
│ Lineární algebra 2                │ 14:00 - 15:30        │ S5   │
│ Počítačové systémy                │ 15:40 - 17:10        │ S3   │
│                                                                 │
├──────────────────────◀ Wednesday / 2. 9. ▶──────────────────────┤
│ Programování 2                    │  9:00 - 10:30        │ S5   │
│ The C Programming Language        │ 10:40 - 12:10        │ SU2  │
│ Počítačové systémy                │ 12:20 - 13:50 (even) │ SW2  │
│ Algoritmy a Datové Struktury      │ 14:00 - 15:30        │ S11  │
│ Úvod do Linuxu                    │ 15:40 - 17:10 (even) │ S5   │
│                                                                 │
├───────────────────────◀ Thursday / 3. 9. ▶──────────────────────┤
│ Architektura počítačů             │  9:00 - 10:30        │ S5   │
│ Matematická analýza 1             │ 12:20 - 13:50        │ S1   │
│ Matematická analýza 1             │ 14:00 - 15:30        │ S3   │
│ Programování 2                    │ 15:40 - 17:10        │ S8   │
│ Úvod do řešení problémů           │ 19:20 - 21:00        │ S3   │
│                                                                 │
├───────────────────────◀ Friday / 28. 8. ▶───────────────────────┤
│ Úvod do Linuxu                    │ 10:40 - 12:10        │ SU2  │
╰─────────────────────────────────────────────────────────────────╯
```

If `<when>` is plain, only a simple list is produced:

```
ADS++-c
ADS-c
ADS-p
AP-p
C-c
DPP-c
DPP-p
IPS-c
LA-c
LA-p
LINUX-c
LINUX-p
MA-c
MA-p
PROG-c
PROG-p
PS-c
PS-p
```

#### `list finals`
Lists finals for all courses. To add a final, one must add the `final` attribute to `info.yaml`:

```
╭───────────────────────────◀ Finals! ▶───────────────────────────────────────╮
│ Algoritmy a Datové Struktury │  4. 6. 2020 │  9:30 │ done            │ S3   │
│ Matematická analýza 1        │  9. 6. 2020 │ 10:00 │ done            │ S5   │
│ Programování 2               │ 10. 6. 2020 │  9:00 │ done            │ S3   │
│ Lineární algebra 2           │ 15. 6. 2020 │  9:00 │ done            │ S9   │
│ Architektura počítačů        │ 18. 6. 2020 │ 13:00 │ done            │ Zoom │
│ Počítačové systémy           │ 26. 6. 2020 │ 10:00 │ 1 day, 19 hours │ Zoom │
╰─────────────────────────────────────────────────────────────────────────────╯
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

#### `open <action> <course>`
Opens something course-related.

Leaving `course` empty selects the ongoing (or upcoming if there is no ongoing) course. One can also add `-?` at the end (where `?` is the first character of the course type) to open the specific course type inside the course folder (example: `alg-c` for "cvičení" (labs) in algorithms). Setting `argument` to `n` or `next` opens the next course. Note that `course` is case and diacritics-insensitive, so `open course ËĎÁüí` is the same as `open course edaui`.

##### `open course <course>`
Open the course with the specified name/abbreviation in the file browser specified in the script configuration.

##### `open website <course>`
Open the website of the course in the file browser specified in the configuration. If multiple websites are found, an option is presented to open one.

##### `open lsf <course>`
Open the LSF site of the course in the file browser specified in the configuration.

_Added because I'm currently getting a Master's degree in Computer Science from the University of Heidelberg and this is the central system they're using._

##### `open notes <course>`
Open the `notes.<note app extensions>` file in the given course's directory in the note app specified in the configuration.
If multiple files are found, an option is presented to open one.

##### `open online <course>`
Open the course's online link in the file browser specified in the configuration.
Meant to be a Zoom (or Zoom-like service) link, which will likely differ from the course's website.

#### `initialize <schedule CSV>`
Initializes a new school year from a CSV in the format from my university's information system (SIS).
For fellow students of MFF UK: `SIS -> Rozvrh NG -> Zobrazit všechny předměty -> CSV`.

#### `homework`
Handles homework-related actions.

##### `list <course name/abbreviation/'all'>`
Lists all unfinished homework.
`course` is in the same form as the `open` command above.
If `all` is specified, all homework (regardless of completeness) is listed.

```
╭───────────────────────────────────────────────◀ Homework ▶───────────────────────────────────────────────╮
│ iqf │ Matematická analýza 1             │ Equations     │ 27. 8. 2020 │ 12:00 │ overdue (1 day, 5 hours) │
│ rgs │ Lineární algebra 2                │ Formulas      │ 30. 8. 2020 │ 13:00 │ 1 day, 19 hours          │
│                                                                                                          │
├───────────────────────────────────────────◀ Without deadline ▶───────────────────────────────────────────┤
│ myb │ Doporučené postupy v programování │ A big project │ -           │ -     │ -                        │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

##### `add or new <course>`
Add a new homework to a given course (same format as `open` above) and open it in the editor specified in `config.py`.

##### `edit or change <uid>`
Edit a homework with the given UID (to find a UID of a homework, use `homework list`).

##### `remove or delete <uid>`
Delete a homework with the given UID.

##### `complete or finish <uid>`
Mark a homework with the given UID as compete.

##### `extrapolate <course>`
Attempt to create a new homework for a given course by looking at the name and date of the previous two.

### Application dependencies
The script calls various external programs for opening notes/websites/folders:

- File explorer: [Ranger](https://wiki.archlinux.org/index.php/Ranger)
- Note taker: [Xournal++](https://github.com/xournalpp/xournalpp)
- Text editor: [Vim](https://www.vim.org/)
- Web browser: [Firefox](https://www.mozilla.org/firefox/)

If you prefer to use other programs, edit `config.py`.

### Folder structure
The script requires a particular folder structure to function properly.
By default, a `courses` folder/symlink (as defined by the `courses_folder` variable in `config.py`) should be placed in the `school` folder of this repository with the following contents:

```
courses
├── Course 1 (abbreviation)
│   ├── tutorial
│   │   └── info.yaml
│   └── lecture
│   │   └── info.yaml
├── Course 2 (abbreviation)
│   ├── tutorial
│   │   └── info.yaml
│   └── lecture
│   │   └── info.yaml
└── courses...
```

The courses should all be in one folder, their folder names being the course name, followed by the course abbreviation (`Algorithms I (ALG)`, for example).
In each of the course folders, at least one of the folder names specified in `school/config.py > course_types` should be present - these are defined by the user and separate the given course tutorial/lecture files.

The `info.yaml` file contains all of the necessary information about the course, such as time, place, email, etc...
Here is the full syntax with sample values:

```
code: 14j1o53

teacher:
    name: John Smith
    email: smith@email.com
    website: john.com
    office: T312
    note: "Consultations from 13:00 to 15:00 on Wednesday."

time:
    day: Wednesday
    start: 14:00
    end: 15:30
    weeks: odd

classroom:
    address: 89 Old Atlantic St. Christiansburg, VA 24073
    number: S11
    floor: 3

finals:
    date: 2020-06-18T13:00:00Z
    classroom: ...

website: https://www.google.com
online: https://zoom.us/j/96931706150

credits: 8
```

All of the root attributes values are optional, so even an empty `.yaml` file is a valid course identifier.

### Flags
The script supports various flags (sometimes):

- `-s`, `--short` - makes the output of the script more concise
- `-f`, `--folder` - specify, where the current courses folder is (overrides `config.py`)
	- useful when you want to operate on the previous semesters but don't want to rewrite configuration

## `md_to_pdf`
Converts markdown files with embedded Xournal++ files to PDF (using Pandoc).
Helpful when doing homework where sketches are required.

### Dependencies

- [Inkscape](https://inkscape.org/)
- [Pandoc](https://pandoc.org/)
- [Xournal++](https://github.com/xournalpp/xournalpp)
