import os

# Slackライブラリ
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# .env読み込み
from dotenv import load_dotenv
load_dotenv()

# modulesフォルダのユーザー定義関数をインポート
from modules.modal import register_modal_handlers # Slackのフォームの関数
from modules.chatgpt import generator_answer_gpt # @GPTでChatGPTを起動させる関数
from modules.search import look_for
from modules.show import select_all_db
from modules.save import store_thread
from modules.message import message
from modules.workflow import workflow_step

from modules.upload import source

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = App(token=SLACK_BOT_TOKEN)
source(app)
look_for(app)
store_thread(app)
select_all_db(app)
register_modal_handlers(app) # Slackのフォーム
generator_answer_gpt(app) # @GPTでChatGPTを起動
message(app)
workflow_step(app)

# アプリを起動します
if __name__ == "__main__":
    SocketModeHandler(app, SLACK_APP_TOKEN).start()
