from pathlib import Path
from typing import Union

from live_template import TemplateParser
from .utils import to_message


class AiogramParser(TemplateParser):
    def __init__(self, templates_dir: Union[str, Path]):
        super().__init__(templates_dir)

    def get_message(self, template_name: str, **kwargs) -> dict:
        template = self.render_template(template_name, **kwargs)
        if not template:
            raise

        return to_message(template)
