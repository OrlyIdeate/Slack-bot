import os
import openai

# Slackライブラリ
from slack_bolt import App
from slack_sdk.web import WebClient
from slack_bolt.adapter.socket_mode import SocketModeHandler

# .env読み込み
from dotenv import load_dotenv
load_dotenv()

# modulesフォルダのユーザー定義関数をインポート
from modules.modal import register_modal_handlers # Slackのフォームの関数
from modules.chatgpt import generator_answer_gpt # @GPTでChatGPTを起動させる関数
from modules.search import search
from modules.show import show
from modules.save import save

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = App(token=SLACK_BOT_TOKEN)
register_modal_handlers(app) # Slackのフォーム
generator_answer_gpt(app) # @GPTでChatGPTを起動
search(app)
show(app)
save(app)


# アプリを起動します
if __name__ == "__main__":
    SocketModeHandler(app, SLACK_APP_TOKEN).start()
