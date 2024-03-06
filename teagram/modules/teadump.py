from .. import loader, utils, __version__
from ..utils import BASE_PATH, BASE_DIR, get_distro
from ..types import Config, ConfigValue

import telethon
import platform
import logging
import atexit
import json
from git import Repo

PATH = f"{BASE_PATH}/dump.json"
REPO = Repo(BASE_DIR)

logger = logging.getLogger()


class DumpMod(loader.Module):
    """Makes dump with information"""

    strings = {"name": "dump"}

    def __init__(self):
        self.config = Config(
            ConfigValue(
                "dump_on_unload",
                "Enables dump on unload",
                False,
                self.get("dump_on_unload"),
                loader.validators.Boolean(),
            )
        )

    def get_token(self):
        try:
            with open(BASE_PATH / "db.json", "r") as file:
                json_data = json.load(file)
                return bool(json_data.get("teagram.bot", {}).get("token"))
        except FileNotFoundError:
            return False

    def get_git_info(
        self, commit: bool = False, url: bool = False, branch: bool = False
    ):
        repo = REPO

        if commit:
            return repo.commit()
        elif url:
            return repo.remotes.origin.url
        elif branch:
            return repo.active_branch.name

    def gen(self) -> dict:
        ver = platform.platform() if "windows" in platform.platform() else get_distro()
        try:
            return {
                "teagram.token": {"token": self.get_token()},
                "teagram.modules": {
                    "modules": [mod.name for mod in self.manager.modules]
                },
                "teagram.version": {
                    "version": __version__,
                    "telethon": telethon.__version__,
                },
                "teagram.platform": {"platform": utils.get_platform(), "os": ver},
                "teagram.git": {
                    "url": self.get_git_info(url=True),
                    "commit": str(self.get_git_info(commit=True)),
                    "branch": str(self.get_git_info(branch=True)),
                },
            }
        except TypeError:
            pass

    async def dump_cmd(self, message):
        result = self.gen()

        with open(PATH, "w") as f:
            json.dump(result, f, indent=4)

        await utils.answer(message, PATH, document=True, caption=self.strings("dumped"))

    @loader.loop(5, autostart=True)
    async def dumploop(self):
        global data, dump
        result = self.gen()
        data = result
        dump = self.get("dump_on_unload")

    @atexit.register
    def create_dump():
        global data, dump

        if dump:
            with open(PATH, "w") as f:
                json.dump(data, f, indent=4)

            logger.info(f"Dump file created, {PATH}") # need to defuse this string.
