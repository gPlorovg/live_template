from pathlib import Path
from typing import Union

from ..storage.storage import TemplateStorage


class TemplateParser:
    def __init__(self, templates_dir: Union[str, Path]):
        self._storage = TemplateStorage(templates_dir, {})

    def get_template(self, template_name: str) -> dict:
        template = self._storage[template_name]
        if template:
            return template.to_dict()
        return {}

    def __getitem__(self, item):
        return self.get_template(item)


if __name__ == "__main__":
    tp = TemplateParser("../templates")
    print(tp["dirrrrr/default_template_with_adjusted_buttons"])
    print(tp["ololo"])
