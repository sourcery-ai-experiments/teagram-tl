#                            ██╗████████╗███████╗██╗░░░░░░█████╗░██╗░░░██╗███████╗
#                            ██║╚══██╔══╝╚════██║██║░░░░░██╔══██╗╚██╗░██╔╝╚════██║
#                            ██║░░░██║░░░░░███╔═╝██║░░░░░███████║░╚████╔╝░░░███╔═╝
#                            ██║░░░██║░░░██╔══╝░░██║░░░░░██╔══██║░░╚██╔╝░░██╔══╝░░
#                            ██║░░░██║░░░███████╗███████╗██║░░██║░░░██║░░░███████╗
#                            ╚═╝░░░╚═╝░░░╚══════╝╚══════╝╚═╝░░╚═╝░░░╚═╝░░░╚══════╝
#                                            https://t.me/itzlayz
#
#                                    🔒 Licensed under the СС-by-NC
#                                 https://creativecommons.org/licenses/by-nc/4.0/

import asyncio
from asyncio import Process
from typing import Union

from telethon import types
from .. import loader, utils


async def bash_exec(command: Union[bytes, str]) -> Process:
    a = await asyncio.create_subprocess_shell(
        command.strip(),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    if not (out := await a.stdout.read(-1)):
        try:
            return (await a.stderr.read(-1)).decode()
        except UnicodeDecodeError:
            return f"Unicode decode error: {(await a.stderr.read(-1))}"
    else:
        try:
            return out.decode()
        except UnicodeDecodeError:
            return f"Unicode decode error: {out}"


@loader.module(name="Terminal", author="teagram")
class TerminalMod(loader.Module):
    """Используйте терминал BASH прямо через 🍵teagram!"""

    strings = {"name": "terminal"}

    async def terminal_cmd(self, message: types.Message, args: str):
        """Use terminal"""
        await utils.answer(message, "☕")

        args = args.strip()
        output = await bash_exec(args)

        await utils.answer(
            message,
            "<emoji document_id=5472111548572900003>⌨️</emoji>"
            f"<b> {self.strings['cmd']}:</b> <pre language='bash'>{args}</pre>\n"
            f"💾 <b>{self.strings['output']}:</b>\n<pre language='bash'>"
            f"{output}"
            "</pre>",
        )
