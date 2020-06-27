"""A configuration file for the school script."""

# the relative path to the folder where the courses are stored
courses_folder = "courses/"


# course types -- labs/lectures/...
# the numbers are ANSI colors that the course type will be painted with (see https://www.lihaoyi.com/post/BuildyourownCommandLinewithANSIescapecodes.html)
# the first letters of each of the courses must differ (for `school o c alg-c`/`school o c alc-p`)
course_types = {
    "cvičení": (155,),
    "přednáška": (153,),
}

# mail settings (for gmail, since that's what I'm using
# feel free to override in private configuration
smtp_address = "smtp.gmail.com"
smtp_port = 465

smtp_login = "to be overwritten by private configuration"
smtp_password = "to be overwritten by private configuration"

# is the same for Gmail but could be different for others
smtp_from = smtp_login


# default handlers for opening course folders/websites/notes...
file_browser = ["ranger"]
web_browser = ["firefox", "-new-window"]
