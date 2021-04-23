import configparser
import fnmatch
import os
import subprocess
import sys


def main():
    config = configparser.ConfigParser()
    config.read("setup.cfg")
    section = "check_permissions"

    default_mode = config.get(section, "default_mode", fallback=None)
    overrides = config.get(section, "overrides", fallback="")

    overrides = [s.strip() for s in overrides.split(",")]
    overrides = [s for s in overrides if s]
    overrides = [s.split(":") for s in overrides]

    if not all([len(s) == 2 for s in overrides]):
        raise Exception

    overrides = dict(overrides)

    p = subprocess.run(
        ["git", "ls-files"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=True,
    )

    filenames = p.stdout.decode().splitlines()

    failed = False
    for filename in filenames:
        info = os.stat(filename)
        mode = oct(info.st_mode)[-3:]

        try:
            expected_mode = next(m for p, m in overrides.items() if fnmatch.fnmatch(filename, p))
        except StopIteration:
            expected_mode = default_mode

        if not expected_mode:
            continue

        if mode != expected_mode:
            print("{}: has mode {}, expected {}".format(filename, mode, expected_mode))
            failed = True

    if failed:
        raise Exception


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(1)
