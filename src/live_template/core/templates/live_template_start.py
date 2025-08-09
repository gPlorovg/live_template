text = """
<b>Hello!</b> 👋 I'm a Live Template Package, ready to assist you. Here are some commands you can use:

• <b>/start_lt</b> - to get here
• <b>/list_template_names</b> - to get list of available templates
"""

parse_mode = "HTML"

buttons = [
    {"text": "Templates", "callback_data": "list_template_names"},
    {"text": "Show all", "callback_data": "list_templates"},
    {"text": "Always retry", "callback_data": "toggle_always_retry"},
]

btn_row_sizes = [1]
