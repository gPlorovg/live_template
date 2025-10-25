import pytest
from live_template import TemplateParser


@pytest.fixture
def parser() -> TemplateParser:
    return TemplateParser("tests/templates")


def test_get_template_existing(parser: TemplateParser):
    result = parser.get_template("test_all")
    assert isinstance(result, dict)
    assert result.get("name") == "test_all"
    assert result.get("text") == "\nTEXT\n"
    assert result.get("parse_mode") == "HTML"
    assert result.get("buttons")[0] == {"text": "BTN1", "callback_data": "btn1"}
    assert result.get("btn_row_sizes")[0] == 1


def test_get_template_existing_nested_text(parser: TemplateParser):
    result = parser["nested_templates/test_all"]
    assert isinstance(result, dict)
    print(result)
    assert result.get("name") == "nested_templates/test_all"
    assert result.get("text") == "\nTEXT\n"
    assert result.get("parse_mode") == "HTML"
    assert result.get("buttons")[0] == {"text": "BTN1", "callback_data": "btn1"}
    assert result.get("btn_row_sizes")[0] == 1


def test_get_template_existing_empty(parser: TemplateParser):
    result = parser.get_template("test_empty")
    assert result.get("name") == "test_empty"
    assert result.get("text") == ""
    assert result.get("parse_mode") == "HTML"
    assert result.get("buttons") is None
    assert result.get("btn_row_sizes") is None


def test_get_template_no_existing(parser: TemplateParser):
    result = parser.get_template("test_no_existing")
    assert result == {}

def test_render_template_format(parser: TemplateParser):
    name = "name"
    result = parser.render_template("test_format", name=name)

    assert result.text == f"\nTEXT {name}\n"
