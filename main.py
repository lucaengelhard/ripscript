import subprocess
import argparse
import pathlib

LOG_LEVELS = {
    "quiet": 0,
    "progress": 1,
    "message": 2,
    "full": 3,
}

parser = argparse.ArgumentParser(prog="ripscript")
parser.add_argument("input type", choices=["disc", "file"])
parser.add_argument("input path", type=pathlib.Path)
parser.add_argument("output directory", type=pathlib.Path)
parser.add_argument("name")

parser.add_argument("-m", "--mode", choices=["info", "rip"], default="rip")
parser.add_argument("-l", "--log-level",
                    choices=list(LOG_LEVELS), default="progress")
parser.add_argument("-s", "--selection-mode",
                    choices=["chapter", "length"], default="chapter")
parser.add_argument("-a", "--amount", type=int, default=1)

parser.add_argument("-t", "--type", choices=["movie", "show"], default="movie")
parser.add_argument("-S", "--season", type=int)
parser.add_argument("-e", "--epiosde", type=int)
parser.add_argument("-p", "--part", type=int)
parser.add_argument("-P", "--part-type",
                    choices=["cd", "dvd", "part", "pt", "disc", "disk"], default="disc")

args = parser.parse_args()


def log(message, level=LOG_LEVELS["progress"]):
    if level <= LOG_LEVELS[args.log_level]:
        print(message)


log(f"Mode: {args.mode}")


# subprocess.run(["makemkvcon", "-r", "--progress=-same", "info", "disc:0"])
