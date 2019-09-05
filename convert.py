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


def generate_random_hex_number(length):
    """Generates a random hexadecimal number (with possible leading zeroes!) of the
    specified length."""
    return "".join(random.choice("0123456789abcdef") for _ in range(length))


def xopp_to_svg(input_file, output_file):
    """Convert a .xopp file to a .svg file using Xournal++."""
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

        # regex to find points of the paths of the svg file objects
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


# check for empty arguments
if len(sys.argv) == 1:
    exit("Nothing to convert!")

# make note of the generated files to remove them after the conversions
generated_files = []

# go through the specified markdown files
for md_file_name in sys.argv[1:]:
    print(f"Processing {md_file_name}:")

    # read the md file
    with open(md_file_name, "r") as f:
        contents = f.read()

        # find each of the .xopp files in the .md file
        for match in compile(r"\[(.*)]\((.+?).xopp\)", MULTILINE).finditer(contents):
            file_label, file_name = match.groups()

            # convert the .xopp file to .svg file(s)
            print(f"- converting {file_name}.xopp to SVG...")
            xopp_to_svg(f"{file_name}.xopp", f"{file_name}.svg")

            # get all .svg files generated from the .xopp file
            file_names = [f[:-4] for f in glob.glob(f"{file_name}*.svg")]

            # covert the .svg files to .png, cropping them in the process
            for file_name in file_names:
                print("- cropping SVG...")
                crop_svg_file(f"{file_name}.svg")

                print(f"- converting {file_name}.svg to PNG...")
                svg_to_png(f"{file_name}.svg", f"{file_name}.png")

                generated_files += [f"{file_name}.svg", f"{file_name}.png"]

            # replace the links to the .xopp files to the .png images
            contents = contents.replace(
                match.group(0),
                "\n\n".join(
                    [f"![{file_label}]({file_name}.png)" for file_name in file_names]
                ),
            )

    print("- generating resulting PDF...")

    # create a dummy .md file for the conversion
    dummy_file_name = generate_random_hex_number(10) + ".md"
    with open(dummy_file_name, "w") as f:
        f.write(contents)

    # covnert the .md file to .pdf
    md_to_pdf(dummy_file_name, md_file_name[:-2] + "pdf")

    generated_files += [dummy_file_name]

    print()

# clean-up after the script is done
print("Cleaning up...")
delete_files(generated_files)

print("Done!\n")
