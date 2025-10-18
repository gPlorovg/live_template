import asyncio
import os
from pathlib import Path
from typing import Union

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from live_template.core.router.base_router import BaseRouter
from live_template.core.storage.storage import Template

from .utils import make_callback_class, to_message, callback_wrapper


class AiogramRouter(BaseRouter, Router):
    TEMPLATE_CALLBACK_DATA = make_callback_class(BaseRouter.TEMPLATE_CALLBACK_ID)

    def __init__(self, templates_dir: Union[str, Path], default_template: dict):
        super().__init__(templates_dir, default_template)
        self._bot = None
        self._setup_handlers()

    async def _send_msg(self, chat_id: int, template: Template):
        await self._bot.send_message(self._chat_id, **to_message(template))

    def _setup_handlers(self):
        @self.startup()
        async def on_startup(bot: Bot):
            self._bot = bot
            self._on_startup()

        self.shutdown()(self._on_shutdown)

        @self.message(Command(AiogramRouter.START_COMMAND))
        async def start(message: Message):
            await self._start(message.chat.id)

        for command in self.command_handlers:
            self.message(Command(command))(self.command_handlers[command])

        for callback in self.callback_handlers:
            self.callback_query(F.data == callback)(
                callback_wrapper(self.callback_handlers[callback])
            )

        @self.callback_query(AiogramRouter.TEMPLATE_CALLBACK_DATA.filter())
        @callback_wrapper
        async def get_template(
            callback_query: CallbackQuery,
            callback_data: AiogramRouter.TEMPLATE_CALLBACK_DATA,
        ):
            await self._get_template(callback_data.name)


async def main():
    from dotenv import load_dotenv

    load_dotenv()
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    lt_router = AiogramRouter("../templates", {})
    dp.include_router(lt_router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
