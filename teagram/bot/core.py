import logging
import asyncio
import sys
import traceback
import inspect

from aiogram import Bot, Dispatcher, exceptions
from aiogram.types import (
    InlineKeyboardMarkup, InlineQuery, InputTextMessageContent,
    InlineQueryResultArticle, InlineQueryResultDocument, InlineQueryResultPhoto
)

from telethon.types import Message, Photo, Document
from telethon import TelegramClient, errors
from telethon.tl.functions.messages import StartBotRequest
from telethon.tl.functions.contacts import UnblockRequest

from typing import Union, NoReturn
from loguru import logger

from .events import Events
from .token_manager import TokenManager

from .. import database, __version__, types, utils


class BotManager(Events, TokenManager):
    """
    Bot Manager class.
    Manages the bot's functionalities.
    """

    def __init__(self, app: TelegramClient, db: database.Database, manager: types.ModulesManager) -> None:
        """
        Initialize the Bot Manager.

        Parameters:
            app (TelegramClient): The client instance.
            db (database.Database): The database instance.
            manager (types.ModulesManager): The modules manager.
        """
        self._app = app
        self._db = db
        self._manager = manager

        self._token = self._db.get("teagram.bot", "token", None)
        self._units = {}
        self.cfg = {}

    async def load(self) -> Union[bool, NoReturn]:
        """
        Load the bot manager.

        Returns:
            Union[bool, NoReturn]: True if loaded successfully, else exits with an error.
        """
        logging.info("Loading bot manager...")
        error_text = "The userbot requires a bot. Resolve the bot creation issue and restart the userbot."

        new = False
        revoke = False

        if not self._token:
            self._token = await self._revoke_token()
            new = True
            revoke = True

        if not self._token:
            new = True
            
            self._token = await self._create_bot()
            if not self._token:
                logging.error(error_text)
                sys.exit(1)

        try:
            self.bot = Bot(self._token, parse_mode="html")
        except (exceptions.ValidationError, exceptions.Unauthorized):
            logging.error("Invalid token. Attempting to recreate the token.")

            result = await self._revoke_token()
            new = True
            revoke = True
            
            if not result:
                self._token = await self._create_bot() or logging.error(error_text) or sys.exit(1)
            else:
                self._token = result

        if new:
            name = (await self.bot.get_me()).username
            await self._app(StartBotRequest(name, name, 'start'))

            if revoke:
                from ..fsm import Conversation

                async with Conversation(self._app, "@BotFather") as conv:
                    try:
                        await conv.ask("/cancel")
                    except errors.UserIsBlockedError:
                        await self._app(UnblockRequest('@BotFather'))
                    
                    await conv.ask("/setinline")
                    await conv.get_response()

                    await conv.ask(self.bot_username)
                    await conv.get_response()

                    await conv.ask("~teagram~ $")
                    await conv.get_response()

                    logger.success("Bot revoked successfully")

        self._db.set('teagram.bot', 'token', self._token)
        self._dp = Dispatcher(self.bot)
        self._register_handlers()

        asyncio.ensure_future(self._dp.start_polling())

        self.bot.manager = self
        return True

    def _register_handlers(self) -> None:
        """
        Register event handlers.
        """
        self._dp.register_message_handler(self._message_handler, lambda _: True, content_types=["any"])
        self._dp.register_inline_handler(self._inline_handler, lambda _: True)
        self._dp.register_callback_query_handler(self._callback_handler, lambda _: True)

    async def invoke_inline(self, inline_id: str, message: Message) -> Message:
        return await utils.invoke_inline(
            message,
            (await self.bot.get_me()).username,
            inline_id
        )
    
    async def form(
        self,
        *,
        title: str,
        description: Union[str, None] = None,
        text: str,
        message: Message, 
        reply_markup: Union[InlineKeyboardMarkup, None] = None,
        photo: Photo = None,
        doc: Document = None
    ):
        unit_id = utils.random_id()
        self._units[unit_id] = {
            'type': 'form',
            'title': title,
            'description': description,
            'text': text,
            'keyboard': reply_markup,
            'message': message,
            'photo': photo,
            'doc': doc,
            'top_msg_id': message.reply_to.reply_to_top_id or message.reply_to.reply_to_msg_id
        }

        try:
            await self.invoke_inline(unit_id, message)
        except Exception as error:
            del self._units[unit_id]

            error = "\n".join(traceback.format_exc().splitlines()[1:])

            await utils.answer(
                message,
                f'Не удалось отправить форму\n'
                f"<code>{error}</code>"
            )
    
    async def _inline_handler(self, inline_query: InlineQuery) -> InlineQuery:
        """
        Inline query event handler.

        Processes incoming inline queries by invoking appropriate inline handlers.

        Args:
            inline_query (InlineQuery): The incoming inline query.

        Returns:
            InlineQuery: The processed inline query.
        """
        if not (query := inline_query.query):
            commands = ""
            for command, func in self._manager.inline_handlers.items():
                if await self._check_filters(func, func.__self__, inline_query):
                    commands += f"\n💬 <code>@{(await self.bot.me).username} {command}</code>"

            message = InputTextMessageContent(
                f"👇 <b>Available Commands</b>\n"
                f"{commands}"
            )

            return await inline_query.answer(
                [
                    InlineQueryResultArticle(
                        id=utils.random_id(),
                        title="Available Commands",
                        input_message_content=message
                    )
                ], cache_time=0
            )
        
        query_ = query.split()

        cmd = query_[0]
        args = " ".join(query_[1:])

        try:
            form = self._units[query]
            text = form.get('text')
            keyboard = form.get('keyboard')

            if not form['photo'] and not form['doc']:
                await inline_query.answer(
                    [
                        InlineQueryResultArticle(
                            id=utils.random_id(),
                            title=form.get('title'),
                            description=form.get('description'),
                            input_message_content=InputTextMessageContent(
                                text,
                                parse_mode='HTML',
                                disable_web_page_preview=True
                            ),
                            reply_markup=keyboard
                        )
                    ]
                )
            elif form['photo']:
                await inline_query.answer(
                    [
                        InlineQueryResultPhoto(
                            id=utils.random_id(),
                            title=form.get('title'),
                            description=form.get('description'),
                            input_message_content=InputTextMessageContent(
                                text,
                                parse_mode='HTML',
                                disable_web_page_preview=True
                            ),
                            reply_markup=keyboard,
                            photo_url=form['photo'],
                            thumb_url=form['photo']
                        )
                    ]
                )
            elif form['doc']:
                await inline_query.answer(
                    [
                        InlineQueryResultDocument(
                            id=utils.random_id(),
                            title=form.get('title'),
                            description=form.get('description'),
                            input_message_content=InputTextMessageContent(
                                text,
                                parse_mode='HTML',
                                disable_web_page_preview=True
                            ),
                            reply_markup=keyboard,
                            document_url=form['doc']
                        )
                    ]
                )
        except KeyError:
            pass
        except Exception as error:
            traceback.print_exc()
        try:
            if (data := self.cfg[cmd]):
                if not args:
                    return await inline_query.answer(
                        [
                            InlineQueryResultArticle(
                                id=utils.random_id(),
                                title="Teagram",
                                description='Укажите значение',
                                input_message_content=InputTextMessageContent(
                                    "❌ Вы не указали значение")
                            )
                        ], cache_time=0
                    )
                else:
                    attr = data['attr']

                    data['cfg'][attr] = utils.validate(args)
                    self._db.set(
                        data['mod'].name,
                        attr,
                        utils.validate(args)
                    )

                    await inline_query.answer(
                        [
                            InlineQueryResultArticle(
                                id=utils.random_id(),
                                title="Вы изменили атрибут!",
                                description='Изменив аргументы вы изменяете атрибут',
                                input_message_content=InputTextMessageContent(
                                    "✔ Вы успешно изменили атрибут!")
                            )
                        ], cache_time=0
                    )
        except KeyError:
            pass

        

        func = self._manager.inline_handlers.get(cmd)
        if not func:
            return await inline_query.answer(
                [
                    InlineQueryResultArticle(
                        id=utils.random_id(),
                        title="Error",
                        input_message_content=InputTextMessageContent(
                            "❌ No such inline command")
                    )
                ], cache_time=0
            )

        if not await self._check_filters(func, func.__self__, inline_query):
            return

        try:
            if (
                len(vars_ := inspect.getfullargspec(func).args) > 3
                and vars_[3] == "args"
            ):
                await func(inline_query, args)
            else:
                await func(inline_query)
        except Exception as error:
            logging.exception(error)

        return inline_query
