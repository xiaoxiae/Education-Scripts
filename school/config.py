"""A configuration file for the school script."""

# the relative path to the folder where the courses are stored
courses_folder = "courses/"


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
