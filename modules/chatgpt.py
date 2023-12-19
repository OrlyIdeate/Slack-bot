import os
from slack_bolt import App
from slack_sdk.web import WebClient
import openai

# .env読み込み
from dotenv import load_dotenv
load_dotenv()

from modules.similarity import get_top_5_similar_texts

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

def generator_answer_gpt(app: App):
    @app.message("@GPT")
    def ret_gpt(message, say):
        openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
        slack_client = WebClient(token=SLACK_BOT_TOKEN)
        message_text = message['text']
        message_channel = message['channel']
        message_thread_ts = message['ts']

        message_text += " これは質問として十分ですか？不十分ですか？十分のときは十分の確認は必要なく、質問の回答だけを表示してください。不十分であれば回答はせずに何が不十分なのかを教えてください。"

        chat_completion = openai_client.chat.completions.create(
            messages=[{"role": "user", "content": message_text}],
            model="gpt-4"
        )
        response_text = chat_completion.choices[0].message.content

        if "この質問は不十分です" not in response_text:
            top_5_similar_texts = get_top_5_similar_texts(message_text)
            response_text+= "\n類似度が高い順:\n\n"
            for similarity, content, url, date in top_5_similar_texts:
                response_text += f"*Content:* {content}\n"
                response_text += f"*URL:* <{url}|Link>\n"
                response_text += f"*Date:* {date}\n\n"
                response_text += "-----------------------------\n"  # 区切り線を追加

        response = slack_client.chat_postMessage(
            channel=message_channel,
            text=response_text,
            thread_ts=message_thread_ts
        )

    @app.event("message")
    def handle_unhandled_message_events(event, logger):
        logger.info(f"未処理のメッセージイベント: {event}")


def chatgpt(message):
        openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
        message_text = message

        chat_completion = openai_client.chat.completions.create(
            messages=[{"role": "user", "content": message_text}],
            model="gpt-4"
        )
        response_text = chat_completion.choices[0].message.content

        top_5_similar_texts = get_top_5_similar_texts(message_text)
        response_text+= "\n類似度が高い順:\n\n"
        for similarity, content, url, date in top_5_similar_texts:
            response_text+=f"Content: {content}, URL: {url}, Date: {date}\n"

        return response_text