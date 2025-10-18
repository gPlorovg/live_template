import functools

from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from live_template.core.storage.storage import Template


def make_callback_class(prefix: str):
    class _Callback(CallbackData, prefix=prefix):
        name: str

    return _Callback


def render_buttons(buttons: list, row_sizes: list) -> InlineKeyboardMarkup:
    ikb = InlineKeyboardBuilder()
    if buttons:
        if all(isinstance(b, list) for b in buttons):
            # Flow for full mapped buttons
            for btn_row in buttons:
                ikb.row(*[InlineKeyboardButton(**btn.to_dict()) for btn in btn_row])
        else:
            # Flow for adjusted buttons
            for btn in buttons:
                ikb.button(**btn.to_dict())

            if row_sizes:
                ikb.adjust(*row_sizes)
            else:
                ikb.adjust(2)

    return ikb.as_markup()


def to_message(template: Template) -> dict:
    return {
        "text": template.text,
        "parse_mode": template.parse_mode,
        "reply_markup": render_buttons(template.buttons, template.btn_row_sizes),
    }


def callback_wrapper(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        callback_query = None
        for arg in args:
            if isinstance(arg, CallbackQuery):
                callback_query = arg
                break
        try:
            await func(*args, **kwargs)
        finally:
            if callback_query:
                await callback_query.answer()

    return wrapper
