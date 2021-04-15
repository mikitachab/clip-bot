import os
import sys

project_dir = os.path.dirname(os.path.dirname(__file__))
bot_dir = os.path.join(project_dir, "bot")

sys.path.append(bot_dir)
