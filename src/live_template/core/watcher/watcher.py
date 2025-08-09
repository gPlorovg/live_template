import asyncio
import functools
import threading
import time
from pathlib import Path

from watchdog.events import FileSystemEvent, PatternMatchingEventHandler
from watchdog.observers import Observer

from ..core import config, log
from ..storage.storage import TemplateStorage
from ..utils.utils import get_name_by_path


def handle_event(func):
    @functools.wraps(func)
    def wrapper(self, event: FileSystemEvent):
        template_name = get_name_by_path(
            event.src_path, self.watcher.template_storage.templates_dir
        )

        now = time.time()
        last = self.last_changed.get(template_name, 0)
        if now - last < self.debounce:
            return

        self.last_changed[template_name] = now

        return func(self, template_name, event=event)

    return wrapper


class TemplateHandler(PatternMatchingEventHandler):
    def __init__(self, watcher: "TemplateWatcher"):
        super().__init__(patterns=["*.py"], ignore_directories=True)
        self.watcher = watcher
        self.last_changed = {}
        self.debounce = 0.5  # seconds

    @handle_event
    def on_modified(self, template_name: str, **kwargs):
        self.watcher.template_storage.add_or_update_template(template_name)
        log.info(f"Template '{template_name}' was changed")
        if config["always_retry"]:
            asyncio.run_coroutine_threadsafe(
                self.watcher.queue.put(("MODIFIED", template_name)), self.watcher.loop
            )

    @handle_event
    def on_created(self, template_name: str, **kwargs):
        self.watcher.template_storage.add_or_update_template(template_name)
        log.info(f"Template '{template_name}' was added")

    @handle_event
    def on_moved(self, template_name: str, event: FileSystemEvent, **kwargs):
        old_template_name = template_name
        try:
            dest_path = Path(event.dest_path)
            new_template_name = get_name_by_path(
                dest_path, self.watcher.template_storage.templates_dir
            )
            self.watcher.template_storage.rename_template(
                old_template_name, new_template_name
            )
            log.info(
                f"Template '{old_template_name}' was renamed to '{new_template_name}'"
            )
        except ValueError:
            self.watcher.template_storage.delete_template(template_name)
            log.info(f"Template '{template_name}' was removed")

    @handle_event
    def on_deleted(self, template_name: str, **kwargs):
        self.watcher.template_storage.delete_template(template_name)
        log.info(f"Template '{template_name}' was removed")


class TemplateWatcher:
    def __init__(
        self,
        storage: TemplateStorage,
        queue: asyncio.Queue,
        loop: asyncio.AbstractEventLoop,
    ):
        self.template_storage = storage
        self.queue = queue
        self.loop = loop
        self.observer = None

    def start_watching(self):
        self.observer = Observer()
        self.observer.schedule(
            TemplateHandler(self), self.template_storage.templates_dir, recursive=True
        )
        observer_thread = threading.Thread(target=self.observer.start, daemon=True)
        observer_thread.start()
        log.info(
            f"Started '{self.template_storage.templates_dir.resolve()}' observing..."
        )


async def main():
    storage = TemplateStorage("../templates", {})
    queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    tw = TemplateWatcher(storage, queue, loop)
    tw.start_watching()

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
