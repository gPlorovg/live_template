import ast
from importlib.abc import Traversable
from pathlib import Path
from typing import Iterable, Union

from ..core import log


def get_path_by_name(template_name: str, templates_dir: Union[str, Path]) -> Path:
    name = Path(template_name).with_suffix(".py")
    path = Path(templates_dir) / name
    if not path.is_file():
        raise ValueError(f"Wrong path to template '{path}'")
    return path


def get_name_by_path(path: Union[str, Path], templates_dir: Union[str, Path]) -> str:
    name = Path(path)
    if not name.suffix == ".py":
        raise ValueError(f"Wrong path to template '{path}'")

    root = Path(templates_dir)
    name = name.relative_to(root).with_suffix("")

    return str(name)


def parse_template(path: Union[str, Path, Traversable]) -> dict:
    if not isinstance(path, Traversable):
        path = Path(path)

    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        data = {}
        for node in tree.body:
            if isinstance(node, ast.Assign):
                target = node.targets[0]
                if isinstance(target, ast.Name) and target.id in {
                    "text",
                    "parse_mode",
                    "buttons",
                    "btn_row_sizes",
                }:
                    data[target.id] = ast.literal_eval(node.value)
        return data
    except (OSError, SyntaxError):
        log.exeption(f"Failed to parse template '{path}'")
        return {}


def get_internal_name_by_path(path: Traversable, templates_dir: Traversable) -> str:
    if not path.name.endswith(".py"):
        raise ValueError(f"Wrong path to template '{path}'")

    if not str(path).startswith(str(templates_dir)):
        raise ValueError(f"Wrong root '{templates_dir}' for path '{path}'")

    return str(path)[len(str(templates_dir)) :].lstrip("/").rstrip(".py")


def get_path_by_internal_name(
    template_name: str, templates_dir: Traversable
) -> Traversable:
    path = templates_dir.joinpath(template_name + ".py")
    if not path.is_file():
        raise ValueError(f"Wrong path to template '{path}'")

    return path


def iter_traversable(path: Traversable, pattern: str = "") -> Iterable:
    if path.is_file() and path.name.endswith(pattern):
        yield path
    elif path.is_dir():
        for child in path.iterdir():
            yield from iter_traversable(child)
