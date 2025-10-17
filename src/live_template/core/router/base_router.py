import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union

from ..core import config, package_root
from ..storage.storage import (
    InlineButton,
    InternalTemplateStorage,
    Template,
    TemplateStorage,
)
from ..watcher.watcher import TemplateWatcher


class BaseRouter(ABC):
    TEMPLATE_CALLBACK_ID = "template"
    START_COMMAND = "start_lt"
    TEMPLATE_CALLBACK_SEP = ":"

    def __init__(self, templates_dir: Union[str, Path], default_template: dict):
        super().__init__()

        self.command_handlers = {}
        self.callback_handlers = {}

        self._templates_dir = Path(templates_dir)
        self._default_template = default_template

        self._internal_templates_dir = package_root / "core" / "templates"
        self._internal_default_template = {"text": "Default template"}
        self._internal_storage = InternalTemplateStorage(
            self._internal_templates_dir, self._internal_default_template
        )

        self._storage = TemplateStorage(self._templates_dir, self._default_template)

        self._tw_queue = asyncio.Queue()
        self._tw_loop = asyncio.get_running_loop()
        self._tw = TemplateWatcher(self._storage, self._tw_queue, self._tw_loop)
        self._tw.start_watching()

        self._chat_id = None
        self._always_retry = False

        self.setup_handlers()

    def setup_handlers(self):
        # self.register_command("lt_start")(self._start)
        self.register_command("list_template_names")(self._list_template_names)

        self.register_callback("list_template_names")(self._list_template_names)
        self.register_callback("toggle_always_retry")(self._toggle_always_retry)
        self.register_callback("list_templates")(self._list_templates)

        # self.register_callback(self._template_callback_id)(self._get_template)

    def register_command(self, command: str):
        def wrapper(func):
            self.command_handlers[command] = func
            return func

        return wrapper

    def register_callback(self, callback: str):
        def wrapper(func):
            self.callback_handlers[callback] = func
            return func

        return wrapper

    # async def handle(self, command: str, *args, **kwargs):
    #     handler = self.handlers.get(command)
    #     if handler:
    #         if inspect.iscoroutinefunction(handler):
    #             return await handler(*args, **kwargs)
    #         else:
    #             loop = asyncio.get_event_loop()
    #             return await loop.run_in_executor(None, lambda: handler(*args, **kwargs))

    @abstractmethod
    async def _send_msg(self, chat_id: int, template: Template):
        pass

    def _template(
        self, template_name: str, is_internal: bool = False
    ) -> Union[Template, None]:
        storage = self._internal_storage if is_internal else self._storage
        template = storage[template_name]
        if not template:
            return None

        return template

    @staticmethod
    def _template_callback(template_name: str):
        return (
            BaseRouter.TEMPLATE_CALLBACK_ID
            + BaseRouter.TEMPLATE_CALLBACK_SEP
            + template_name
        )

    def _on_startup(self):
        asyncio.create_task(self._always_retry_dispatcher())

    async def _on_shutdown(self):
        await self._tw_queue.put(None)

    # Command: lt_start
    async def _start(self, chat_id: int):
        self._chat_id = chat_id
        template = self._template("live_template_start", is_internal=True)
        await self._send_msg(self._chat_id, template)

    # Command: list_template_names
    # Callback: list_template_names
    async def _list_template_names(self, *args, **kwargs):
        template_names = sorted(self._storage.names())
        template_name = "list_templates" if template_names else "no_templates"
        template = self._template(template_name, is_internal=True)
        template.buttons = []
        for name in template_names:
            template.buttons.append(InlineButton(name, self._template_callback(name)))

        await self._send_msg(self._chat_id, template)

    # Callback: toggle_always_retry
    async def _toggle_always_retry(self, *args, **kwargs):
        self._always_retry = not self._always_retry
        template = self._template(
            f"always_retry_{str(self._always_retry).lower()}", is_internal=True
        )
        config["always_retry"] = self._always_retry
        await self._send_msg(self._chat_id, template)

    # Callback: list_templates
    async def _list_templates(self, *args, **kwargs):
        for name, template in sorted(self._storage.list()):
            await self._send_msg(self._chat_id, Template(name=name, text=name))
            await self._send_msg(self._chat_id, template)

    # Callback: self._template_callback(template_name)
    async def _get_template(self, template_name: str):
        template = self._template(template_name)
        await self._send_template(template)

    async def _send_template(self, template: Template):
        await self._send_msg(self._chat_id, template)
        if not self._always_retry:
            await self._send_retry_btn(template.name)

    async def _always_retry_dispatcher(self):
        while True:
            message = await self._tw_queue.get()
            if message is None:
                break

            if self._always_retry and self._chat_id:
                action, template_name = message
                template = self._template(template_name)
                await self._send_template(template)

    async def _send_retry_btn(self, template_name: str):
        template = self._template("retry_btn", is_internal=True)
        template.buttons = [
            InlineButton(template_name, self._template_callback(template_name))
        ]
        await self._send_msg(self._chat_id, template)
