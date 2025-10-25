import datetime as dt

import pytest

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.types import (
    Update, Message, Chat, User, CallbackQuery as TgCallbackQuery,
    InlineKeyboardMarkup
)
from aiogram.methods import SendMessage, AnswerCallbackQuery, EditMessageText, \
    EditMessageReplyMarkup

from live_template import AiogramRouter


TEMPLATES_DIR = "tests/templates"
DEFAULT_TEMPLATE = {}

# ---------- вспомогательные фабрики ----------

def make_message(text: str = "/start_lt") -> Message:
    return Message(
        message_id=1,
        date=dt.datetime.now(dt.timezone.utc),
        chat=Chat(id=100, type="private"),
        from_user=User(id=100, is_bot=False, first_name="Test"),
        text=text,
    )

def make_update_message(text: str = "/start_lt") -> Update:
    return Update(update_id=1, message=make_message(text))

def make_update_callback(data: str) -> Update:
    cq = TgCallbackQuery(
        id="cq1",
        from_user=User(id=100, is_bot=False, first_name="Test"),
        chat_instance="ci",
        data=data,
        message=make_message("btn"),
    )
    return Update(update_id=2, callback_query=cq)


# ---------- фикстуры инфраструктуры ----------
@pytest.fixture
def router() -> AiogramRouter:
    return AiogramRouter(TEMPLATES_DIR, DEFAULT_TEMPLATE)

@pytest.fixture
def dp(router: AiogramRouter) -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(router)
    return dp

@pytest.fixture
def bot() -> Bot:
    return Bot("42:TEST")


@pytest.fixture
def record_api(monkeypatch):
    calls = []

    async def fake_make_request(self: AiohttpSession, bot, payload, timeout=None):
        calls.append(payload)

        if isinstance(payload, SendMessage):
            raw = {
                "message_id": 1,
                "date": int(dt.datetime.now(dt.timezone.utc).timestamp()),
                "chat": {"id": payload.chat_id, "type": "private"},
                "text": payload.text,
                "parse_mode": payload.parse_mode,
                "reply_markup": payload.reply_markup,
            }

            return Message.model_validate(raw)

        if isinstance(payload, (EditMessageText, EditMessageReplyMarkup, AnswerCallbackQuery)):
            return True

        return True

    monkeypatch.setattr(AiohttpSession, "make_request", fake_make_request, raising=False)
    return calls


# ---------- тесты ----------
def flatten_split_buttons(data) -> tuple[set, set]:
    texts = set()
    callbacks = set()
    if isinstance(data, InlineKeyboardMarkup):
        assert len(data.inline_keyboard) != 0
        assert len(data.inline_keyboard[0]) != 0
        btns = [x for row in data.inline_keyboard for x in row]
        texts = set([b.text for b in btns])
        callbacks = set([b.callback_data for b in btns])
    elif isinstance(data, list):
        texts = set([b["text"] for b in data])
        callbacks = set([b["callback_data"] for b in data])

    return texts, callbacks

def check_buttons(inline_keyboard, must_be_btns):
    texts, callbacks = flatten_split_buttons(inline_keyboard)
    must_texts, must_callbacks = flatten_split_buttons(must_be_btns)
    assert texts == must_texts, f"TEXT {texts ^ must_texts}"
    assert callbacks == must_callbacks, f"CALLBACK {callbacks ^ must_callbacks}"


@pytest.mark.asyncio
async def test_start_command(dp: Dispatcher, bot: Bot, record_api):
    """
    /start_lt → роутер должен запомнить chat_id и отправить внутренний стартовый шаблон.
    """
    await dp.emit_startup(bot)

    await dp.feed_update(bot, make_update_message("/start_lt"))
    send_calls = [resp for resp in record_api if isinstance(resp, SendMessage)]
    assert send_calls, f"no SendMessage calls, got: {record_api}"
    data = send_calls[-1]
    assert data.chat_id == 100
    assert len(data.text) != 0
    assert data.parse_mode == "HTML"

    buttons = [
        {"text": "Templates", "callback_data": "list_template_names"},
        {"text": "Show all", "callback_data": "list_templates"},
        {"text": "Always retry", "callback_data": "toggle_always_retry"},
    ]
    check_buttons(data.reply_markup, buttons)



@pytest.mark.asyncio
async def test_template(dp: Dispatcher, bot: Bot, router: AiogramRouter, record_api):
    """
    callback 'template:<name>' → сначала отправляется сам шаблон, затем retry-кнопка.
    Используем внешний шаблон 'test_all' из tests/templates.
    """
    await dp.emit_startup(bot)
    template_name = "test_all"
    cb_data = f"{router.TEMPLATE_CALLBACK_ID}:{template_name}"
    await dp.feed_update(bot, make_update_message("/start_lt")) # получить chat_id
    record_api.clear()
    await dp.feed_update(bot, make_update_callback(cb_data))
    send_calls = [resp for resp in record_api if isinstance(resp, SendMessage)]
    assert len(send_calls) == 2, f"expected 2 SendMessage calls, got: {len(send_calls)}"

    template, retry = send_calls[-2:]

    assert template.chat_id == 100
    assert template.text == "\nTEXT\n"
    assert template.parse_mode == "HTML"
    buttons = [
        {"text": "BTN1", "callback_data": "btn1"},
    ]
    check_buttons(template.reply_markup, buttons)

    assert retry.chat_id == 100
    assert retry.text == "\nRetry?\n"
    assert retry.parse_mode == "HTML"

    assert len(retry.reply_markup.inline_keyboard) != 0
    assert len(retry.reply_markup.inline_keyboard[0]) != 0
    retry_btn = retry.reply_markup.inline_keyboard[0][0]

    assert retry_btn.text == template_name
    assert retry_btn.callback_data == f"{router.TEMPLATE_CALLBACK_ID}:{template_name}"


@pytest.mark.asyncio
async def test_list_template_names(dp: Dispatcher, bot: Bot, router: AiogramRouter, record_api):
    """
    /list_template_names → должна прийти клавиатура со списком имён шаблонов.
    """
    await dp.emit_startup(bot)

    await dp.feed_update(bot, make_update_message("/start_lt"))
    record_api.clear()
    await dp.feed_update(bot, make_update_message("/list_template_names"))
    send_calls = [resp for resp in record_api if isinstance(resp, SendMessage)]
    assert send_calls, f"no SendMessage calls, got: {record_api}"

    data = send_calls[-1]
    assert data.chat_id == 100
    assert data.text == "\n📂 Templates list:\n"
    assert data.parse_mode == "HTML"
    templates = ["test_all", "test_btn", "test_btn_row", "test_empty", "test_format",
                 "nested_templates/test_all", "nested_templates/test_empty"]
    buttons = [
        {"text": template, "callback_data": f"{router.TEMPLATE_CALLBACK_ID}:{template}"}
        for template in templates
    ]
    check_buttons(data.reply_markup, buttons)


@pytest.mark.asyncio
async def test_toggle_always_retry(dp: Dispatcher, bot: Bot, router: AiogramRouter, record_api):
    """
    callback 'toggle_always_retry' → переключает флаг и отправляет внутренний шаблон
    'always_retry_true/false'. Проверяем, что сообщение ушло.
    """
    await dp.emit_startup(bot)

    await dp.feed_update(bot, make_update_message("/start_lt"))
    record_api.clear()
    await dp.feed_update(bot, make_update_callback("toggle_always_retry"))
    assert router._always_retry is True

    await dp.feed_update(bot, make_update_callback("toggle_always_retry"))
    assert router._always_retry is False

    send_calls = [resp for resp in record_api if isinstance(resp, SendMessage)]
    assert send_calls, f"no SendMessage calls, got: {record_api}"
    enable, disable = send_calls[-2:]
    assert enable.chat_id == 100
    assert enable.text == "\nAlways retry active!\n"
    assert enable.parse_mode == "HTML"

    assert disable.chat_id == 100
    assert disable.text == "\nAlways retry disabled!\n"
    assert disable.parse_mode == "HTML"


@pytest.mark.asyncio
async def test_list_templates(dp: Dispatcher, bot: Bot, record_api):
    """
    callback 'list_templates' → роутер отправляет пары сообщений:
    1) имя шаблона как текст
    2) сам шаблон
    """
    await dp.emit_startup(bot)

    await dp.feed_update(bot, make_update_message("/start_lt"))
    record_api.clear()
    await dp.feed_update(bot, make_update_callback("list_templates"))
    send_calls = [resp for resp in record_api if isinstance(resp, SendMessage)]
    assert send_calls, f"no SendMessage calls, got: {record_api}"
    must_template_names = {"test_all", "test_btn", "test_btn_row", "test_empty", "test_format",
                 "nested_templates/test_all", "nested_templates/test_empty"}
    msgs = [d.text for d in send_calls]
    template_names = msgs[::2]
    assert set(template_names) == must_template_names, (f"TEMPLATE NAMES:"
                                                    f" {set(template_names) ^ must_template_names}")
    tname = "test_all"
    t = send_calls[msgs.index(tname) + 1]
    assert t.chat_id == 100
    assert t.text == "\nTEXT\n"
    assert t.parse_mode == "HTML"
    buttons = [
        {"text": "BTN1", "callback_data": "btn1"},
    ]
    check_buttons(t.reply_markup, buttons)
