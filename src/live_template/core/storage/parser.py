from pathlib import Path
from typing import Union

from .storage import TemplateStorage, Template


class TemplateParser:
    def __init__(self, templates_dir: Union[str, Path]):
        self._storage = TemplateStorage(templates_dir, {})

    def get_template(self, template_name: str) -> dict:
        template = self._storage[template_name]
        if template:
            return template.to_dict()
        return {}

    def render_template(self, template_name: str, **kwargs) -> Template:
        """
        :param template_name: name of template. user / to separate parts
        :param kwargs: parameters for template text formating
        :return: Template object
        """
        template = self._storage[template_name]
        if template and template.text:
            template.text = template.text.format(**kwargs)

        return template

    def set_storage(self, storage: TemplateStorage):
        """
        WARNING!!! MAY BE UNSTABLE! DO NOT USE IN PRODUCTION ENVIRONMENT!
        :param storage: your lt router storage with realtime updatable templates
        :return:
        """
        self._storage = storage

    def __getitem__(self, item):
        return self.get_template(item)


if __name__ == "__main__":
    tp = TemplateParser("../templates")
    print(tp["dirrrrr/default_template_with_adjusted_buttons"])
    print(tp["ololo"])
