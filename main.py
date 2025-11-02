import subprocess
import argparse
import pathlib
import os
import csv

LOG_LEVELS = {
    "quiet": 0,
    "progress": 1,
    "message": 2,
    "full": 3,
}

parse_state = {
    "current_process": "",
    "titles": []
}

parser = argparse.ArgumentParser(prog="ripscript")
parser.add_argument("input_type", choices=["disc", "file"])
parser.add_argument("input_path", type=pathlib.Path)
parser.add_argument("output_directory", type=pathlib.Path)
parser.add_argument("name")

parser.add_argument("-m", "--mode", choices=["info", "rip"], default="rip")
parser.add_argument("-l", "--log-level",
                    choices=list(LOG_LEVELS), default="progress")
parser.add_argument("-s", "--selection-mode",
                    choices=["chapter", "length"], default="chapter")
parser.add_argument("-a", "--amount", type=int, default=1)

parser.add_argument("-t", "--type", choices=["movie", "show"], default="movie")
parser.add_argument("-S", "--season", type=int)
# TODO: Allow multiple episodes
parser.add_argument("-e", "--episode", type=int)
parser.add_argument("-p", "--part", type=int)
parser.add_argument("-P", "--part-type",
                    choices=["cd", "dvd", "part", "pt", "disc", "disk"],
                    default="disc")

args = parser.parse_args()


def log(message, level=LOG_LEVELS["progress"]):
    if level <= LOG_LEVELS[args.log_level]:
        print(message)


def seasonString(i):
    if i is None:
        return ""
    return f"Season {i}"


def split_line(line: str):
    return next(csv.reader([line]))


def safe_split(line: str, expected: int):
    split = split_line(line)

    while len(split) < expected:
        split.append("")

    return split[0:expected]


def parse_line(line):
    parts = line.split(":", 1)
    identifier = parts[0]
    content = parts[1] if len(parts) > 1 else ""

    match identifier:
        case "PRGV":
            # Progress bar values for current and total progress
            # PRGV:current,total,max
            # current - current progress value
            # total - total progress value
            # max - maximum possible value for a progress bar, constant
            current, total, max = safe_split(content, 3)

            current = int(current)
            total = int(total)
            max = int(max)

            percent = current * 100 / max

            log(f"{parse_state["current_process"]
                   } - {percent}% ({current}/{max})")

        case "PRGT" | "PRGC":
            # Current and total progress title
            # PRGC:code,id,name
            # PRGT:code,id,name
            # code - unique message code
            # id - operation sub-id
            # name - name string
            code, id, name = safe_split(content, 3)
            parse_state["current_process"] = name

        case "DRV":
            # Drive scan messages
            # DRV:index,visible,enabled,flags,drive name,disc name
            # index - drive index
            # visible - set to 1 if drive is present
            # enabled - set to 1 if drive is accessible
            # flags - media flags, see AP_DskFsFlagXXX in apdefs.h
            # drive name - drive name string
            # disc name - disc name string
            index, visible, enabled, flags, drive_name, disc_name = safe_split(
                content, 6)

            log(f"Drive {index} is {"visible" if visible == 1 else "not visible"} and {
                "enabled" if enabled == 1 else "not enabled"}", LOG_LEVELS["full"])

        case "MSG":
            # Message output
            # MSG:code,flags,count,message,format,param0,param1,...
            # code - unique message code, should be used to identify particular string in language-neutral way.
            # flags - message flags, see AP_UIMSG_xxx flags in apdefs.h
            # count - number of parameters
            # message - raw message string suitable for output
            # format - format string used for message. This string is localized and subject to change, unlike message code.
            # paramX - parameter for message

            code, flags, count, message, format, paramX = safe_split(
                content, 6)

            log(message, LOG_LEVELS["message"])

        case "TCOUNT":
            # Disc information output messages
            # TCOUNT:count
            # count - titles count
            log(content, LOG_LEVELS["full"])

        case "CINFO" | "TINFO" | "SINFO":
            # Disc, title and stream information
            # CINFO:id,code,value
            # TINFO:id,code,value
            # SINFO:id,code,value

            # id - attribute id, see AP_ItemAttributeId in apdefs.h
            # code - message code if attribute value is a constant string
            # value - attribute value
            id, code, _unkown, value = safe_split(content, 4)

        case _:
            log(f"Unhandled stdout: {line}", LOG_LEVELS["message"])


# Print command info
log("")
log(f"Mode: {args.mode}")
log(f"Log level: {args.log_level} ({LOG_LEVELS[args.log_level]})")
log(f"Title selection mode: {args.selection_mode}")
log("")
log(f"Input type: {args.input_type}")
log(f"Input path: {args.input_path}")
log(f"Name: {args.name}")

if args.type == "show":
    if args.season is not None:
        log(f"Season: {args.season}")
    if args.episode is not None:
        log(f"Episode: {args.episode}")

if args.part is not None:
    log(f"Part: {args.part}")

if args.mode == "rip":
    log(f"Output parent directory: {args.output_directory}")
    media_dir = pathlib.Path(args.output_directory,
                             args.name, seasonString(args.season))
    log(f"Media directory: {media_dir}")
    os.makedirs(media_dir, exist_ok=True)


log("Parsing media data")
infoproc = subprocess.Popen(["makemkvcon", "-r", "--progress=-same",
                            "info", f"{args.input_type}:{args.input_path}"],
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


for line in infoproc.stdout:
    parse_line(line)

infoproc.wait()
