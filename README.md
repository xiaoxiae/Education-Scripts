# Lecture Notes Scripts
This repository contains scripts to simplify note-taking for CS-related courses and lectures.

## md_to_pdf
Converts markdown files with embedded Xournal++ files to PDF.

Dependencies:
- [Inkscape](https://inkscape.org/)
- [Pandoc](https://pandoc.org/)
- [Xournal++](https://github.com/xournalpp/xournalpp)

For additional information, run `./md_to_pdf -h`.

## school
Perform various school-related tasks, like printing course schedule or opening a course directory.

Dependencies:
- [Xournal++](https://github.com/xournalpp/xournalpp)
- [Ranger](https://wiki.archlinux.org/index.php/Ranger)
- [Firefox](https://www.mozilla.org/firefox/)
- [unidecode](https://pypi.org/project/Unidecode/) (Python module)
- [pyyaml](https://pyyaml.org/wiki/PyYAMLDocumentation) (Python module)

Supported functionality (printed by running `./school`):
```
list courses        List information about the courses.
     finals         List dates of all finals.
     timeline       List the courses in a timeline.
cron                Add crontab notifications for all courses.
browse              Run 'fzf' on the course folder, returning the match.
send                Send an email to the email of the course.
open course         Open the course's folder in Ranger.
     website        Open the course's website in FireFox.
     notes          Open the course's notes in Xournal++.
```


