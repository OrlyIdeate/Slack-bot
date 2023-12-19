from slack_bolt import App
from slack_sdk import WebClient
import os

from dotenv import load_dotenv
load_dotenv()

from modules.similarity import get_embedding, get_top_5_similar_texts

def search(app: App):
    @app.message("@search")
    def ret_gpt(message, say):
        slack_client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
        message_text = message['text']
        message_channel = message['channel']
        message_thread_ts = message['ts']

        top_5_similar_texts = get_top_5_similar_texts(get_embedding(message_text))
        # 結果を表示
        response_text = "*検索結果*:\n\n"

        for similarity, content, url, date in top_5_similar_texts:
            response_text += f"*Content:* {content}\n"
            response_text += f"*URL:* <{url}|Link>\n"
            response_text += f"*Date:* {date}\n\n"
        # スレッド内に返信を送信
        response = slack_client.chat_postMessage(
            channel=message_channel,
            text=response_text,
            thread_ts=message_thread_ts
        )