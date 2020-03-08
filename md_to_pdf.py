import os, glob
from subprocess import Popen, PIPE  # shell commands
from re import sub, compile, MULTILINE
import random
import argparse, shlex, sys  # command line interaction
from typing import List


class CommandError(Exception):
    """A custom exception that is raised when a system command returns a stderr."""

    pass


def run_shell_command(command: List[str], ignore_errors: bool = False) -> None:
    """Run a shell command. If stderr is not empty, the function will terminate the
    script (unless specified otherwise) and print the error message."""
    _, stderr = map(
        lambda b: b.decode("utf-8").strip(),
        Popen(command, stdout=PIPE, stderr=PIPE).communicate(),
    )

    # possibly raise an exception
    if not ignore_errors and stderr != "":
        raise CommandError(
            f"\n{command[0].capitalize()} error:\n| " + stderr.replace("\n", "\n| ")
        )


def generate_random_hex_number(length: int) -> str:
    """Generates a random hexadecimal number (with possible leading zeroes!) of the
    specified length."""
    return "".join(random.choice("0123456789abcdef") for _ in range(length))


def xopp_to_svg(input_file: str, output_file: str) -> None:
    """Convert a .xopp file to a .svg file using Xournal++. Note that xournalpp errors
    are ignored by default, since stderr produces warnings."""
    run_shell_command(
        ["xournalpp", f"--create-img={output_file}", input_file], ignore_errors=True
    )


def svg_to_pdf(input_file: str, output_file: str) -> None:
    """Convert a .svg file to a .pdf file using InkScape."""
    run_shell_command(
        ["inkscape", "-C", "-z", f"--file={input_file}", f"--export-pdf={output_file}"]
    )


def md_to_pdf(input_file: str, output_file: str, parameters: List[str]) -> None:
    """Convert a .md file to a .pdf file using Pandoc."""
    run_shell_command(["pandoc", input_file, "-o", output_file, *parameters])


def crop_svg_file(file_name: str, margin: float = 0) -> None:
    """Crop the specified .svg file.
    TODO: add support for cropping files that include text."""

    with open(file_name, "r") as svg_file:
        contents = svg_file.read()

        # set the default values for the coordinates we're trying to find
        inf = float("inf")
        min_x, min_y, max_x, max_y = inf, inf, -inf, -inf

        # find all paths and their respective descriptions
        paths = compile(r'<path(.+?)d="(.+?)"', MULTILINE).finditer(contents)
        next(paths)  # skip the first one, which is always a solid color background

        for path in paths:
            coordinate_parts = path.group(2).strip().split(" ")
            m_count, l_count = coordinate_parts.count("M"), coordinate_parts.count("L")

            # ignore the paper grid coordinates (alternating m/l commands) and don't
            # ignore pen strokes (since they're one m and one l command)
            if m_count == l_count and m_count + l_count > 2:
                continue

            # get only the coordinate numbers
            coordinates = [float(c) for c in coordinate_parts if not c.isalpha()]

            # check for min/max
            for x, y in zip(coordinates[::2], coordinates[1::2]):
                min_x, max_x = min(min_x, x), max(max_x, x)
                min_y, max_y = min(min_y, y), max(max_y, y)

        # adjust for margins
        min_x -= margin
        min_y -= margin
        max_x += margin
        max_y += margin

        # add/update svg values
        substitutions = (
            (r'<svg(.*)width="(.+?)pt', f'<svg\\1width="{max_x - min_x}pt'),  # width
            (r'<svg(.*)height="(.+?)pt', f'<svg\\1height="{max_y - min_y}pt'),  # height
            (r"<svg(.+)>", f'<svg\\1 x="{min_x}" y="{min_y}">'),  # min x and y
            (
                r'<svg(.*)viewBox="(.*?)"(.*)>',
                f'<svg\\1viewBox="{min_x} {min_y} {max_x - min_x} {max_y - min_y}"\\3>',
            ),  # viewbox
        )

        for pattern, replacement in substitutions:
            contents = sub(pattern, replacement, contents)

    # overwrite the file
    with open(file_name, "w") as svg_file:
        svg_file.write(contents)


def get_argument_parser() -> argparse.ArgumentParser:
    """Returns the ArgumentParser object for the script."""
    parser = argparse.ArgumentParser(
        description="Convert markdown files with embedded Xournal++ files to pdf.",
        epilog="\n  ".join(
            [
                "examples:",
                "py md_to_pdf.py -a                               | convert all .md files",
                "py md_to_pdf.py -s -f README.md                  | silently convert README.md",
                "py md_to_pdf.py -a -p='--template=eisvogel.tex'  | use a pandoc template",
            ]
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # clean-up after the script
    parser.add_argument(
        "-c",
        "--no-cleanup",
        dest="cleanup",
        action="store_false",
        help="don't cleanup cache files generated by the script",
    )

    # supress Xournal++ file embedding
    parser.add_argument(
        "-x",
        "--no-xopp-files",
        dest="embed_xopp_files",
        action="store_false",
        help="don't embed Xournal++ files",
    )

    # silent
    parser.add_argument(
        "-s",
        "--silent",
        dest="silent",
        action="store_true",
        help="prevent the script from outputting any messages",
    )

    # svg margins
    parser.add_argument(
        "-m",
        "--margins",
        dest="margins",
        metavar="M",
        type=int,
        default=15,
        help="set the margins around the cropped Xournal++ files (in points, default 15)",
    )

    # pandoc parameters
    parser.add_argument(
        "-p",
        "--pandoc-parameters",
        dest="pandoc_parameters",
        metavar="P",
        default=[],
        nargs=argparse.REMAINDER,
        help="specify pandoc parameter(s) used in the conversion",
    )

    # use a script template
    parser.add_argument(
        "-t",
        "--template",
        dest="template",
        metavar="T",
        nargs="?",
        default="",
        help="use a pre-made template found in md_to_pdf.templates; if the flag is"
        + "used and no template is specified, the first one in the file is used",
    )

    # either convert all files, only specific files or use a template
    group = parser.add_mutually_exclusive_group(required=True)

    # all .md files
    group.add_argument(
        "-a",
        "--all-files",
        dest="files",
        default=[],
        action="store_const",
        const=glob.glob("*.md"),
        help="convert all Markdown files in the current directory",
    )

    # only specific files
    group.add_argument(
        "-f",
        "--files",
        dest="files",
        default=[],
        metavar="F",
        nargs="+",
        help="the name(s) of the markdown file(s) to convert to pdf",
    )

    return parser


def throw_parsing_error(reason: str, line: str = "", line_num: int = -1, pos: int = -1):
    """Returns a formatted string describing the error that occurred during the parsing
    of the template file."""
    # if the position of the error on a line is not specified, print only the reason
    if line == "" or line_num == -1 or pos == -1:
        print(f"Error parsing template file: {reason}.")
        sys.exit()
    else:
        # for measuring where to put the ^
        error_line = f"| line {line_num}: "

        print(
            "\n".join(
                (
                    f"Error parsing template file: {reason}.",
                    error_line + line,
                    f"|{' ' * (len(error_line) - 1 + pos)}^",
                )
            )
        )
        sys.exit()


def skip_whitespace(reason: str, line: str, line_num: int, pos: int):
    """Return the index of the first non-whitespace character in a string, or exit with
    a parsing error with the specified reason if none was found."""
    for pos in range(pos, len(line)):
        if not line[pos] in {" ", "\t"}:
            return pos
    else:
        throw_parsing_error(reason, line, line_num, pos)


# get the parser and parse the commands
parser = get_argument_parser()
arguments = parser.parse_args()


def print_message(*args):
    """A print() wrapper that does nothing when the silent argument is specified."""
    if not arguments.silent:
        print(*args)


# if the template flag was used, parse the additional arguments from the template file
if arguments.template != "":
    with open(f"{__file__[:-3]}.templates", "r") as f:
        for n, line in enumerate(map(lambda s: s.strip(), f.read().splitlines())):
            # ignore comments
            if line[0] == "#":
                continue

            template_names = []
            parameters = ""

            i = 0
            while i < len(line):
                # parse the template name
                for j in range(i, len(line)):
                    # allow alphanumerics and [_-]
                    if not (line[j].isalnum() or line[j] in "_-"):
                        break
                else:
                    throw_parsing_error("missing parameters", line, n, j)

                # if no name was read, an invalid character is present in the name
                if i == j:
                    throw_parsing_error("invalid template name character", line, n, i)
                else:
                    template_names.append(line[i:j])

                # should find either , or :, since we just read a template name
                i = skip_whitespace("expected , or :", line, n, j)

                if line[i] == ",":
                    i = skip_whitespace("missing template name", line, n, i + 1)
                    continue
                elif line[i] == ":":
                    i = skip_whitespace("missing template parameters", line, n, i + 1)

                    parameters = shlex.split(line[i:])
                    break

            # parse first template if none was specified, or the matching one
            if arguments.template == None or arguments.template in template_names:
                arguments = parser.parse_args(sys.argv[1:] + parameters)
                break
        else:
            # if no template matched the name, throw an error
            throw_parsing_error(f"template '{arguments.template}' not found")


# make note of the generated files to remove them after the conversions
generated_files = []

# go through the specified markdown files
for md_file_name in arguments.files:
    try:
        # get the name of the folder and the name of the file (for a status message)
        folder, file_name = map(
            os.path.basename, (os.path.split(os.path.abspath(md_file_name)))
        )

        # read the markdown file
        print_message(f"Reading '{folder}{os.path.sep}{file_name}':")
        with open(md_file_name, "r") as f:
            contents = f.read()

            if arguments.embed_xopp_files:
                # find each of the .xopp files in the .md file
                for match in compile(r"\[(.*)]\((.+?).xopp\)", MULTILINE).finditer(
                    contents
                ):
                    file_label, file_name = match.groups()

                    # convert the .xopp file to .svg file(s)
                    print_message(f"- converting {file_name}.xopp to SVG...")
                    xopp_to_svg(f"{file_name}.xopp", f"{file_name}.svg")

                    # get all .svg files generated from the .xopp file
                    file_names = [f[:-4] for f in glob.glob(f"{file_name}*.svg")]

                    # covert the .svg files to .pdf, cropping them in the process
                    for file_name in file_names:
                        # add the names first (to possibly be cleaned up later)
                        generated_files += [f"{file_name}.svg", f"{file_name}.pdf"]

                        print_message("- cropping SVG...")
                        crop_svg_file(f"{file_name}.svg", arguments.margins)

                        print_message(f"- converting {file_name}.svg to PDF...")
                        svg_to_pdf(f"{file_name}.svg", f"{file_name}.pdf")

                    # replace the links to the .xopp files to the .pdf images
                    contents = contents.replace(
                        match.group(0),
                        "\n\n".join(
                            [
                                f"![{file_label}]({file_name}.pdf)"
                                for file_name in file_names
                            ]
                        ),
                    )

        print_message("- generating resulting PDF...")

        # create a dummy .md file for the conversion
        dummy_file_name = f"{generate_random_hex_number(20)}.md"
        with open(dummy_file_name, "w") as f:
            f.write(contents)

        # add the names first (to possibly be cleaned up later)
        generated_files += [dummy_file_name]

        # convert the .md file to .pdf
        md_to_pdf(
            dummy_file_name, f"{md_file_name[:-3]}.pdf", arguments.pandoc_parameters
        )

        print_message()
    except FileNotFoundError:
        print("- file not found, skipping")
    except IsADirectoryError:
        print("- file is a directory, skipping")
    except UnicodeDecodeError:
        print("- file is not UTF-8, skipping")
    except CommandError as e:
        print(e)
    except Exception:
        print("- an error occurred when reading the file, skipping")


# clean-up after the script is done
if arguments.cleanup:
    if len(generated_files) == 0:
        print_message("Nothing to clean, done!")
    else:
        print_message("Cleaning up...")
        for f in generated_files:
            os.remove(f)

        print_message("Done!")
