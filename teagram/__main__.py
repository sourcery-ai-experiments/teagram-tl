import sys

if sys.version_info < (3, 8, 0):
    print("Needs Python 3.8 or higher")
    sys.exit(1)

import asyncio
import argparse

from .main import Main
from .logger import init_logging

from contextlib import suppress

parser = argparse.ArgumentParser()
parser.add_argument("--disable-web", action="store_true", help="Disable auth with web")
parser.add_argument("--rnd-session", action="store_true", help="Random session name")
parser.add_argument("--port", help="Set port for web", type=int, required=False)

if __name__ == "__main__":
    init_logging()

    with suppress(KeyboardInterrupt):
        main = Main(parser.parse_args())
        asyncio.run(main.main())
