import sys
import asyncio
import argparse

if sys.version_info < (3, 9, 0):
    print("Needs python 3.9 or higher")
    sys.exit(1)

from .main import Main
from .logger import init_logging
from contextlib import suppress

parser = argparse.ArgumentParser()
parser.add_argument("--disable-web", action="store_true", help="Disable auth with web")
parser.add_argument("--rnd-session", action="store_true", help="Random session name")

if __name__ == "__main__":
    init_logging()

    with suppress(KeyboardInterrupt):
        args = parser.parse_args()
        main = Main(args).main
        asyncio.run(main())
