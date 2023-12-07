import os
from dotenv import load_dotenv
from openai import OpenAI
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from modules.modal import register_modal_handlers # Slackのフォームの処理

# .envから環境変数を読み込む
load_dotenv()

# ボットトークンとソケットモードハンドラーを使ってアプリを初期化します
app = App(token=os.getenv("SLACK_BOT_TOKEN"))

register_modal_handlers(app) # Slackのフォームの処理

####################################################################################################

@app.message("@GPT")
def ret_gpt(message, say):
    client = OpenAI(
        # defaults to os.environ.get("OPENAI_API_KEY")
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    message_text = message['text']
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": message_text,
            }
        ],
        model="gpt-4",
    )
    message_content = chat_completion.choices[0].message.content
    say(message_content)

# 上までで処理できなかった場合の例外処理
@app.event("message")
def handle_unhandled_message_events(event, logger):
    logger.info(f"未処理のメッセージイベント: {event}")

###########################################################################################

# アプリを起動します
if __name__ == "__main__":
    SocketModeHandler(app, os.getenv("SLACK_APP_TOKEN")).start()
