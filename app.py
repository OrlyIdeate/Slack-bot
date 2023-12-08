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
from modules.modal import register_modal_handlers # Slackのフォーム
from modules.similarity import get_top_5_similar_texts # 上位5つの類似データ取得

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = App(token=SLACK_BOT_TOKEN)
register_modal_handlers(app) # Slackのフォーム

####################################################################################################

@app.message("@GPT")
def ret_gpt(message, say):
    openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
    slack_client = WebClient(token=SLACK_BOT_TOKEN)
    message_text = message['text']
    message_channel = message['channel']
    message_thread_ts = message['ts']

    # ChatGPTへの問い合わせ
    chat_completion = openai_client.chat.completions.create(
        messages=[{"role": "user", "content": message_text}],
        model="gpt-4"
    )
    response_text = chat_completion.choices[0].message.content

    top_5_similar_texts = get_top_5_similar_texts(message_text) # 上位5件の類似データを取得
    response_text+= "\n類似度が高い順:\n\n"
    for similarity, content, url, date in top_5_similar_texts:
        response_text+=f"Content: {content}, URL: {url}, Date: {date}\n"
    # スレッド内に返信を送信
    response = slack_client.chat_postMessage(
        channel=message_channel,
        text=response_text,
        thread_ts=message_thread_ts
    )

# 上までで処理できなかった場合の例外処理
@app.event("message")
def handle_unhandled_message_events(event, logger):
    logger.info(f"未処理のメッセージイベント: {event}")

###########################################################################################

# アプリを起動します
if __name__ == "__main__":
    SocketModeHandler(app, SLACK_APP_TOKEN).start()
