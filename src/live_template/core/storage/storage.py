"""
This module contains TemplateStorage class that implements key-value storage where key is name of
template and value is object of Template class. Storage deal with template names and
translate it to file names to check exists.
"""

from dataclasses import asdict, dataclass
from enum import Enum
from importlib.abc import Traversable
from pathlib import Path
from typing import Union

from ..core import log, package_root
from ..utils.utils import (
    get_internal_name_by_path,
    get_name_by_path,
    get_path_by_internal_name,
    get_path_by_name,
    iter_traversable,
    parse_template,
)


@dataclass
class InlineButton:
    text: str
    callback_data: str

    def to_dict(self):
        return asdict(self)


class ParseMode(Enum):
    HTML = "HTML"
    MARKDOWN = "MARKDOWN"
    MARKDOWN_V2 = "MARKDOWN_V2"


@dataclass
class Template:
    name: str
    text: str = ""
    parse_mode: ParseMode = ParseMode.HTML
    buttons: Union[list[list[InlineButton]], list[InlineButton], None] = None
    btn_row_sizes: Union[list[int], None] = None

    def to_dict(self):
        return asdict(self)

    def __post_init__(self):
        # Convert parse_mode form a string to ParseMode
        if isinstance(self.parse_mode, str):
            try:
                self.parse_mode = ParseMode[self.parse_mode]
            except KeyError:
                log.exception(
                    f"Unacceptable value for parse_mode: {self.parse_mode}\n"
                    f"Acceptable values: "
                    f"{' | '.join([mode.value for mode in ParseMode])}"
                )
                return

        # Convert buttons from a one- or two-dimensional list of dicts to
        # one- or two-dimensional list of InlineButtons
        def to_inline_button(obj: Union[dict, InlineButton]) -> InlineButton:
            return InlineButton(**obj) if isinstance(obj, dict) else obj

        if self.buttons:
            try:
                if all(isinstance(b, list) for b in self.buttons):
                    self.buttons = [
                        [to_inline_button(btn) for btn in row] for row in self.buttons
                    ]
                elif all(isinstance(b, dict) for b in self.buttons):
                    self.buttons = [to_inline_button(btn) for btn in self.buttons]
                else:
                    raise ValueError

            except ValueError:
                log.exception(f"Unacceptable value for buttons: {self.buttons}\n")


class BaseTemplateStorage:
    def __init__(self, templates_dir: Union[str, Path], default_template: dict):
        self._storage: dict[str, Template] = {}
        self.default_template = default_template
        self.templates_dir = Path(templates_dir)

    def add_or_update_template(self, template_name: str):
        path = get_path_by_name(template_name, self.templates_dir)

        try:
            data = parse_template(path)
            for k in ("text", "parse_mode", "buttons", "btn_row_sizes"):
                if k not in data and k in self.default_template:
                    data[k] = self.default_template[k]
            data["name"] = template_name
            template = Template(**data)

            self._storage[template_name] = template

        except Exception:
            log.exception(f"Failed to add or update template '{template_name}'")

    def _load_templates(self):
        for file in self.templates_dir.rglob("*.py"):
            try:
                self.add_or_update_template(get_name_by_path(file, self.templates_dir))
            except ValueError:
                log.exception("Failed to load template")

        log.info("Loaded " + str(self))

    def names(self):
        return list(self._storage.keys())

    def list(self):
        return list(self._storage.items())

    def get_template(self, template_name: str) -> Union[Template, None]:
        try:
            return self._storage[template_name]
        except KeyError:
            log.exception(f"No template with name '{template_name}'")
            return None

    def __str__(self):
        return "templates: " + ", ".join(map(lambda s: f"'{s}'", self.names()))

    def __getitem__(self, template_name: str) -> Template:
        return self.get_template(template_name)

    def __contains__(self, template_name: str) -> bool:
        return template_name in self._storage


class TemplateStorage(BaseTemplateStorage):
    def __init__(self, templates_dir: Union[str, Path], default_template: dict):
        super().__init__(templates_dir, default_template)

        if not self.templates_dir.is_dir():
            raise RuntimeError(
                f"Package cannot work without templates directory. Bad path:"
                f" {self.templates_dir.resolve()}"
            )

        self._load_templates()

    def rename_template(self, old_template_name: str, new_template_name: str):
        if old_template_name in self._storage:
            if new_template_name not in self._storage:
                self._storage[new_template_name] = self._storage[old_template_name]
                del self._storage[old_template_name]
            else:
                log.warning(f"New template name '{new_template_name}' already exists!")
        else:
            log.warning(f"Old template name '{old_template_name}' doesn't exists!")

    def delete_template(self, template_name: str):
        if template_name in self._storage:
            del self._storage[template_name]
        else:
            log.warning(f"Template '{template_name}' doesn't exists!")


class InternalTemplateStorage(BaseTemplateStorage):
    def __init__(self, templates_dir: Traversable, default_template: dict):
        super().__init__("", default_template)
        self.templates_dir = templates_dir

        if not self.templates_dir.is_dir():
            raise RuntimeError("Internal Storage bad templates directory!")

        self._load_templates()

    def _load_templates(self):
        for file in iter_traversable(self.templates_dir):
            try:
                self._add(get_internal_name_by_path(file, self.templates_dir))
            except ValueError:
                log.exception("Failed to load template")

        log.info("Loaded " + str(self))

    def _add(self, template_name: str):
        try:
            data = parse_template(
                get_path_by_internal_name(template_name, self.templates_dir)
            )
            for k in ("text", "parse_mode", "buttons", "btn_row_sizes"):
                if k not in data and k in self.default_template:
                    data[k] = self.default_template[k]
            data["name"] = template_name
            template = Template(**data)

            self._storage[template_name] = template
        except Exception:
            log.exception(f"Failed to add or update template '{template_name}'")


def main():
    TemplateStorage("../templates", {})
    InternalTemplateStorage(package_root.joinpath("templates"), {})


if __name__ == "__main__":
    main()
