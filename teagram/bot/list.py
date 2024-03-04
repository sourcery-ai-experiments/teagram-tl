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


import functools
import traceback
import logging
import typing

from telethon.types import Message

from aiogram.types import (
    CallbackQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineQuery,
)

from .. import utils

logger = logging.getLogger(__name__)


class List:
    def __init__(self):
        self.pages = []

    async def list(self, message: Message, strings: typing.List[str], **kwargs):
        """
        :param message: Message
        :param strings: List with strings
        """
        if not isinstance(strings, list):
            logger.error("Invalid type. `strings` must be list, got %s", type(strings))

            return

        for string in strings:
            if len(string) > 4096:
                logger.error("String length must be lower than 4096")

                return

        unit_id = utils.random_id()
        self._units[unit_id] = {
            "type": "list",
            "message": message,
            "message_id": message.id,
            "top_msg_id": utils.get_topic(message),
            "current_index": 0,
            "strings": strings,
            **kwargs,
        }

        try:
            msg = await self.invoke_unit(unit_id, message)
        except Exception:
            logger.exception("Error while sending list")

            await (message.edit if message.out else message.reply)(
                "❌ <code>{}</code>".format(
                    "\n".join(traceback.format_exc().splitlines())
                )
            )

        return msg

    async def _handle_page(self, call: CallbackQuery, page: int, unit_id: str = None):
        _page = self._units[unit_id]
        if isinstance(page, str):
            await self.delete_unit_message(call, unit_id)
            return

        if page >= len(_page["strings"]):
            await call.answer("Invalid page", show_alert=True)
            return

        self._units[unit_id]["current_index"] = page
        try:
            await self.bot.edit_message_text(
                inline_message_id=call.inline_message_id,
                text=_page["strings"][page],
                reply_markup=self.list_markup(unit_id),
            )
        except Exception:
            logger.exception("Can't edit list")
            await call.answer("Error, check logs", show_alert=True)

    def list_markup(self, unit_id: str):
        page = self._units[unit_id]
        current_page = page["current_index"]

        callback = functools.partial(self._handle_page, unit_id=unit_id)
        pages = []

        async def empty(*args, **kwargs):
            pass

        # «
        # ‹
        # ›
        # »

        total = len(page["strings"])
        if current_page < 0:
            current_page = total + current_page
            prev_page = current_page
        else:
            prev_page = current_page - 1

        next_page = current_page + 1

        pages += [
            {"text": f"‹- {prev_page}", "args": (prev_page), "callback": callback},
            {"text": current_page + 1, "callback": empty},
            {"text": f"{next_page + 1} -›", "args": (next_page), "callback": callback},
        ]

        return self._generate_markup([pages])

    async def list_inline_handler(self, inline_query: InlineQuery):
        for key, unit in self._units.copy().items():
            if inline_query.query == key and unit["type"] == "list":
                try:
                    await inline_query.answer(
                        [
                            InlineQueryResultArticle(
                                id=utils.random_id(),
                                title="Teagram list",
                                input_message_content=InputTextMessageContent(
                                    unit["strings"][0],
                                    "HTML",
                                    disable_web_page_preview=True,
                                ),
                                reply_markup=self.list_markup(inline_query.query),
                            )
                        ],
                        cache_time=120,
                    )
                except Exception:
                    traceback.print_exc()
