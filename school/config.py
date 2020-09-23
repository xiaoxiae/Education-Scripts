"""A configuration file for the school script."""

# the relative path to the folder where the courses are stored
courses_folder = "courses/"


# settings regarding course types -- labs/lectures/...
# the numbers are ANSI colors that the course type will be painted with
# see https://www.lihaoyi.com/post/BuildyourownCommandLinewithANSIescapecodes.html
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
text_editor = ["vim"]
note_app = ["xournalpp", ".xopp"]  #  [app, extension]


# default handler for Cron class notifications
# the first argument after this command is the body of the notification
notify_command = "DISPLAY=:0 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus dunstify 'School Schedule'"

notify_started_message = "právě začal předmět"  # course started message
notify_no_more_courses = "dnes již žádný další předmět není"  # no more courses today
notify_next_course_message = (
    "další předmět je <i>{0} ({1})</i>, "  # {0} is course name, {1} is course type
    "který začíná <i>{2} minut</i> po tomto "  # {2} is minutes till next course
    "v učebně <i>{3}</i>"  # {3} is the location
)
