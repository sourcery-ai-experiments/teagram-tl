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

import typing

from .. import loader, utils, validators
from ..validators import ValidationError
from ..bot.types import InlineCall

from aiogram import Bot
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent


@loader.module("Config", "teagram")
class TeaConfigMod(loader.Module):
    strings = {"name": "teaconfig"}

    def __init__(self):
        self._bot: Bot = self.inline.bot

    def keywords(self, config, option: str) -> str:
        validator = getattr(config.config[option], "validator")
        if not validator:
            return ""

        if isinstance(validator, validators.Hidden):
            return "👥 <b>Hidden validator</b>"

        keywords = getattr(validator.type, "keywords", "")
        if not keywords:
            return ""

        keys = list(keywords.items())
        text = ", ".join(f"<b>{key[0]}</b> - <code>{key[1]}</code>" for key in keys)

        return f"🔎 {text}"

    def hide(self, validator, value: str) -> str:
        if not value:
            return value
        if isinstance(validator, validators.Hidden):
            return "".join("*" for _ in range(len(value)))

        return value

    async def change(
        self, call: InlineCall, module: str, option: str, value: typing.Any
    ):
        module = self.lookup(module)
        config = module.config

        config[option] = value
        config.config[option].value = value

        module.set(option, value)

        markup = [
            {
                "text": self.strings("back"),
                "callback": self.configure,
                "args": (module.name),
            }
        ]

        await call.edit(
            self.strings("edit_value"), self.inline._generate_markup(markup)
        )

    async def set_default_value(self, call: InlineCall, module: str, option: str):
        module = self.lookup(module.lower())
        config = module.config
        value = config.get_default(option)

        config[option] = value
        config.config[option].value = value

        module.set(option, value)
        markup = [
            {
                "text": self.strings("back"),
                "callback": self.configure,
                "args": (module.name),
            }
        ]

        await call.edit(
            self.strings("edit_default_value"), self.inline._generate_markup(markup)
        )

    async def set_value_inline_handler(self, call: InlineQuery):
        if not getattr(self, "_id", {}).get("id", ""):
            return

        option = self._id["option"]
        module = self._id["module"]
        value = utils.validate(call.query.replace("set_value ", ""))

        module = self.lookup(module)
        config = module.config
        markup = [
            {"text": self.strings("back"), "callback": self.configure, "args": (module)}
        ]

        try:
            config[option] = value
        except ValidationError:
            return await call.answer(
                [
                    InlineQueryResultArticle(
                        id=utils.random_id(),
                        title="Error",
                        input_message_content=InputTextMessageContent(
                            self.strings("keywords_error")
                        ),
                        reply_markup=self.inline._generate_markup(markup),
                    )
                ]
            )

        return await call.answer(
            [
                InlineQueryResultArticle(
                    id=utils.random_id(),
                    title="Teagram",
                    description="Configuring",
                    input_message_content=InputTextMessageContent(
                        self.strings("sure_change")
                    ),
                    reply_markup=self.inline._generate_markup(
                        [
                            {
                                "text": self.strings("change"),
                                "callback": self.change,
                                "args": (self._id["module"], option, value),
                            }
                        ]
                        + [markup]
                    ),
                )
            ]
        )

    async def back_modules(self, call: InlineCall):
        markup = [
            {
                "text": module.name.title(),
                "callback": self.configure,
                "args": (module.name),
            }
            for module in self.manager.modules
            if getattr(self.lookup(module.name), "config", "")
        ]

        await call.edit(
            self.strings("choose_module"),
            reply_markup=self.inline._generate_markup(utils.sublist(markup)),
        )

    async def show_value(self, call: InlineCall, module: str, option: str, value: str):
        config = self.lookup(module).config
        docstring = config.get_doc(option)
        default = config.get_default(option)
        value = config[option]

        if callable(docstring):
            docstring = docstring()

        markup = [
            [
                {"text": self.strings("change"), "input": "set_value"},
                {
                    "text": self.strings("default"),
                    "callback": self.set_default_value,
                    "args": (module, option),
                },
            ],
            [
                {
                    "text": self.strings("hide"),
                    "callback": self.configure_value,
                    "args": (module, option),
                }
            ],
            [
                {
                    "text": self.strings("back"),
                    "callback": self.configure,
                    "args": (module),
                }
            ],
        ]
        await call.edit(
            (
                self.strings("configure_value").format(module, option)
                + f"❔ {docstring}\n\n"
                + self.strings("default_value").format(utils.escape_html(default))
                + self.strings("current_value").format(utils.escape_html(value))
                + self.keywords(config, option)
            ),
            self.inline._generate_markup(markup),
        )

    async def configure(self, call: InlineCall, module: str):
        markup = [
            {"text": option, "callback": self.configure_value, "args": (module, option)}
            for option in self.lookup(module).config
        ] + [[{"text": self.strings("back"), "callback": self.back_modules}]]
        await call.edit(
            self.strings("choose_value"), self.inline._generate_markup(markup)
        )

    async def configure_value(self, call: InlineCall, module: str, option: str):
        config = self.lookup(module).config
        docstring = config.get_doc(option)
        default = config.get_default(option)
        validator = getattr(config.config[option], "validator", None)
        value = config[option]

        if callable(docstring):
            docstring = docstring()

        _id = utils.random_id(5)
        self._id = {"id": _id, "module": module.lower(), "option": option}

        markup = [
            [
                {"text": self.strings("change"), "input": "set_value"},
                {
                    "text": self.strings("default"),
                    "callback": self.set_default_value,
                    "args": (module, option),
                },
            ],
            (
                [
                    {
                        "text": self.strings("show"),
                        "callback": self.show_value,
                        "args": (module, option, value),
                    }
                ]
                if isinstance(validator, validators.Hidden)
                else []
            ),
            [
                {
                    "text": self.strings("back"),
                    "callback": self.configure,
                    "args": (module),
                }
            ],
        ]

        value = self.hide(validator, value)
        await call.edit(
            (
                self.strings("configure_value").format(module, option)
                + f"❔ {docstring}\n\n"
                + self.strings("default_value").format(utils.escape_html(default))
                + self.strings("current_value").format(utils.escape_html(value))
                + self.keywords(config, option)
            ),
            self.inline._generate_markup(markup),
        )

    async def opencfg(self, call: InlineCall):
        await call.edit(
            text=self.strings("choose_module"),
            reply_markup=self.inline._generate_markup(
                utils.sublist(
                    [
                        {
                            "text": module.name.title(),
                            "callback": self.configure,
                            "args": (module.name),
                        }
                        for module in self.manager.modules
                        if getattr(self.lookup(module.name), "config", "")
                    ]
                )
            ),
        )

    @loader.command()
    async def cfgcmd(self, message):
        markup = [{"text": self.strings("open"), "callback": self.opencfg}]

        await self.inline.form(
            message=message, text="⚙ <b>Teagram | Config</b>", reply_markup=markup
        )
        await message.delete()
