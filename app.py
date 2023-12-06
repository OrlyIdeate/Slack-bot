import os
from dotenv import load_dotenv
from openai import OpenAI
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient


# .envから環境変数を読み込む
load_dotenv()

# ボットトークンとソケットモードハンドラーを使ってアプリを初期化します
app = App(token=os.getenv("SLACK_BOT_TOKEN"))

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

# モーダル表示時のアクション
@app.shortcut("modal-shortcut")
def open_modal(ack, body, client, context):
    ack()
    # モーダルを送信する
    modal_view = {
        "type": "modal",
        "callback_id": "modal-submit",
        "title": {"type": "plain_text", "text": "Chat-GPTに質問"},
        "submit": {"type": "plain_text", "text": "送信"},
        # 見た目の調整は https://app.slack.com/block-kit-builder を使うと便利です
        "blocks": [
            {
                "type": "input",
                "block_id": "question-block",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "input_field"
                },
                "label": {
                    "type": "plain_text",
                    "text": "質問を入力してください"
                }
            }
        ]
    }

    client.views_open(
        trigger_id=body["trigger_id"],
        view=modal_view
    )

# モーダルでの入力送信時のアクション
@app.view("modal-submit")
def modal_submit(ack, body, client, respond):
    ack()
    # フォーム（モーダル）で受け取った質問が入ってる変数
    question = body["view"]["state"]["values"]["question-block"]["input_field"]["value"]
    # 入力されたデータをチャンネルに送信する
    channel_id = "C067ALJLXRQ"  # メッセージを送信するチャンネルのIDに置き換えてください

    client.chat_postMessage(
        channel=channel_id,
        text=f"受け取った質問: {question}"
    )


# アプリを起動します
if __name__ == "__main__":
    SocketModeHandler(app, os.getenv("SLACK_APP_TOKEN")).start()
