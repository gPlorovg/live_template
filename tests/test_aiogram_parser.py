import pytest
from live_template import AiogramParser

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@pytest.fixture
def parser_aiogram() -> AiogramParser:
    return AiogramParser("tests/templates")

def test_get_message_existing(parser_aiogram: AiogramParser):
    msg = parser_aiogram.get_message("test_all")

    assert isinstance(msg, dict)

    assert msg["text"] == "\nTEXT\n"
    assert msg["parse_mode"] == "HTML"

    assert isinstance(msg["reply_markup"], InlineKeyboardMarkup)
    ik = msg["reply_markup"]
    assert len(ik.inline_keyboard) == 1
    assert len(ik.inline_keyboard[0]) == 1

    btn: InlineKeyboardButton = ik.inline_keyboard[0][0]
    assert btn.text == "BTN1"
    assert btn.callback_data == "btn1"


def test_get_message_empty(parser_aiogram: AiogramParser):
    msg = parser_aiogram.get_message("test_empty")

    assert msg["text"] == ""
    assert msg["parse_mode"] == "HTML"

    ik = msg["reply_markup"]
    assert isinstance(ik, InlineKeyboardMarkup)
    assert ik.inline_keyboard == []


def test_render_template_formatting_affects_message(parser_aiogram: AiogramParser):
    name = "NAME"
    msg = parser_aiogram.get_message("test_format", name=name)
    assert msg["text"] == f"\nTEXT {name}\n"
