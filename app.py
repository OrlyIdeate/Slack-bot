import os
import numpy as np
import pandas as pd
from datetime import datetime
import pickle
import mysql.connector
import openai

# Slackライブラリ
from slack_bolt import App
from slack_sdk.web import WebClient
from slack_bolt.adapter.socket_mode import SocketModeHandler

# .env読み込み
from dotenv import load_dotenv
load_dotenv()

from modules.modal import register_modal_handlers # Slackのフォームの処理

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")

app = App(token=SLACK_BOT_TOKEN)
register_modal_handlers(app) # Slackのフォームの処理

####################################################################################################

client = openai.OpenAI(api_key=OPENAI_API_KEY)

def get_embedding(text):
    response = client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
    )
    # 応答から埋め込みデータを取得する正しい方法を使用
    embedding = response.data[0].embedding
    return embedding
# コサイン類似度計算式
def cosine_similarity(vec_a, vec_b):
    dot_product = np.dot(vec_a, vec_b)
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    return dot_product / (norm_a * norm_b)

def get_top_5_similar_texts(message_text):
    vector1 = get_embedding(message_text)
    config = {
        'user': 'root',
        'password': 'hIxhon-9xinto-wernuf',
        'host': '34.135.69.97',
        'database': 'test1',
    }
    db_connection = mysql.connector.connect(**config)
    cursor = db_connection.cursor()
    query = "SELECT content, vector, url, date FROM phase4;"
    cursor.execute(query)
    rows = cursor.fetchall()
    similarity_list = []
    for content, vector_bytes, url, date in rows:
        vector2 = pickle.loads(vector_bytes)
        similarity = cosine_similarity(vector1, vector2)
        similarity_list.append((similarity, content, url, date))
    similarity_list.sort(reverse=True)
    return similarity_list[:5]

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

    top_5_similar_texts = get_top_5_similar_texts(message_text)
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
