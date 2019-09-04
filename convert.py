import os, shutil, glob  # folder + path utilities
from subprocess import call, DEVNULL  # executing shell commands
from re import sub, compile, MULTILINE  # for cropping

import random  # generating random strings for cache

import sys  # command line interaction


def run_shell_command(command, silent=True):
    """Run a shell command."""
    if silent:
        call(command, stderr=DEVNULL, stdout=DEVNULL)
    else:
        call(command)


def generate_random_string(length):
    """Generates a random hexadecimal number of specified length."""
    return "".join(random.choice("0123456789abcdef") for _ in range(length))


def xopp_to_svg(input_file, output_file):
    """Convert a .xopp file to a .svg file using Xournal++ command line interface."""
    run_shell_command(["xournalpp", f"--create-img={output_file}", input_file])


def svg_to_png(input_file, output_file):
    """Convert a .svg file to a .png file using ImageMagic."""
    run_shell_command(
        ["convert", "-density", "400", "-scale", "175%", input_file, output_file]
    )


def md_to_pdf(input_file, output_file):
    """Convert a .md file to a .pdf file using Pandoc."""
    run_shell_command(
        [
            "pandoc",
            input_file,
            "-o",
            output_file,
            "--template",
            "eisvogel.tex",
            "--listings",
        ]
    )


def crop_svg_file(file_name, margin=15):
    """Crop the specified .svg file."""
    # for setting default values of the coordinates of the points of the svg
    inf = float("inf")

    with open(file_name, "r") as svg_file:
        # set the default values
        min_x, min_y, max_x, max_y = inf, inf, -inf, -inf
        contents = svg_file.read()

        # regex to find points of the paths of the svg
        regex = compile(
            r'<path(.*?)d="M ([0-9.]+) ([0-9.]+) L ([0-9.]+) ([0-9.]+) "(.*?)\/>',
            MULTILINE,
        )

        # find all the x and y coordinates
        for match in regex.finditer(contents):
            x1, y1, x2, y2 = map(float, match.groups()[1:-1])

            # check for min/max coordinates
            min_x, max_x = min(min_x, x1, x2), max(max_x, x1, x2)
            min_y, max_y = min(min_y, y1, y2), max(max_y, y1, y2)

        # increase the margins
        min_x -= margin
        min_y -= margin
        max_x += margin
        max_y += margin

        # replace width and height of the svg file
        contents = sub(
            r'<svg(.*)width="(.+?)pt',
            f'<svg\\1width="{max_x - min_x}pt',
            sub(
                r'<svg(.*)height="(.+?)pt',
                f'<svg\\1height="{max_y - min_y}pt',
                contents,
            ),
        )

        # append minimum x and y
        contents = sub(r"<svg(.+)>", f'<svg\\1 x="{min_x}" y="{min_y}">', contents)

        # change viewbox
        contents = sub(
            r'<svg(.*)viewBox="(.*?)"(.*)>',
            f'<svg\\1viewBox="{min_x} {min_y} {max_x - min_x} {max_y - min_y}"\\3>',
            contents,
        )

    # overwrite the file
    with open(file_name, "w") as svg_file:
        svg_file.write(contents)


def delete_files(files):
    """Deletes all of the files specified in the list."""
    for f in files:
        os.remove(f)


# make note of the generated files to remove them all after the conversions
generated_files = []

# go through the specified markdown files
for md_file_name in sys.argv[1:]:
    # for finding the links to xournal files
    xournal_regex = compile(r"\[(.*)]\((.+?).xopp\)", MULTILINE)

    # read the md file
    with open(md_file_name, "r") as md_file:
        contents = md_file.read()

        # find each of the .xopp files in the .md file
        for match in xournal_regex.finditer(contents):
            xopp_file_name = match.group(2)

            # perform the conversions and the croppings
            xopp_to_svg(xopp_file_name + ".xopp", xopp_file_name + ".svg")
            crop_svg_file(xopp_file_name + ".svg")
            svg_to_png(xopp_file_name + ".svg", xopp_file_name + ".png")

            generated_files += [xopp_file_name + ".svg", xopp_file_name + ".png"]

    # generate a dummy md file with the substitutions
    dummy_file_name = generate_random_string(10) + ".md"
    with open(dummy_file_name, "w") as output_file:
        output_file.write(sub(r"\[(.*)]\((.+?).xopp\)", r"![\1](\2.png)", contents))

    # convert the file to pdf
    md_to_pdf(dummy_file_name, md_file_name[:-2] + "pdf")

    generated_files += [dummy_file_name]

# clean-up after the script is done
delete_files(generated_files)
