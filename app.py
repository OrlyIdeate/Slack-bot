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
from modules.save import save
from modules.message import message
from modules.kit import generate_slack_message

from slack_sdk import WebClient
import json

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = App(token=SLACK_BOT_TOKEN)
register_modal_handlers(app) # Slackのフォーム
generator_answer_gpt(app) # @GPTでChatGPTを起動
search(app)
save(app)
message(app)

slack_client = WebClient(token=SLACK_BOT_TOKEN)
slack_message = generate_slack_message()
response = slack_client.chat_postMessage(
    channel="C067ALJLXRQ",
    blocks=slack_message["blocks"]
)
print("起動しました")

@app.action("send_button-action")
def handle_send_button_action(ack, body, logger):
    input_text = body["view"]["state"]["values"]["block_id"]["plain_text_input-action"]["value"]
    logger.info(f"入力された文字列: {input_text}")
    ack()

# アプリを起動します
if __name__ == "__main__":
    SocketModeHandler(app, SLACK_APP_TOKEN).start()
