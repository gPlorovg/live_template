text = """
<b>Hello!</b> 👋 I'm a bot, ready to assist you. Here are some commands you can use:

• <b>/start</b> - start the conversation with the bot 🚀  
• <b>/help</b> - get help with using the bot ❓  
• <b>/info</b> - learn more about the bot ℹ️

   <i>If you have any questions, just let me know!</i> 
"""

parse_mode = "HTML"

buttons = [
    {"text": "Button1_1", "callback_data": "b1_1"},
    {"text": "Button1_2", "callback_data": "b1_2"},
    {"text": "Button1_3", "callback_data": "b1_3"},
    {"text": "Button2_1", "callback_data": "b2_1"},
]

btn_row_sizes = [3, 1]
