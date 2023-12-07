import os
import pandas as pd
import pickle
import openai
import mysql.connector
import numpy as np
from openai import OpenAI
from slack_bolt import App
from slack_sdk.web import WebClient 
from slack_bolt.adapter.socket_mode import SocketModeHandler
from datetime import datetime

# ボットトークンとソケットモードハンドラーを使ってアプリを初期化します
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

####################################################################################################

client = openai.OpenAI(
    # defaults to os.environ.get(“OPENAI_API_KEY”)
    api_key="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",
)

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

####################################################################################################

# 'hello' を含むメッセージをリッスンします
# 指定可能なリスナーのメソッド引数の一覧は以下のモジュールドキュメントを参考にしてください：
# https://slack.dev/bolt-python/api-docs/slack_bolt/kwargs_injection/args.html
@app.message("siri")
def message_hello(message, say):
    # イベントがトリガーされたチャンネルへ say() でメッセージを送信します
    say(
        blocks=[
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"<@{message['user']}> 私はsiriじゃありませんよ？"},
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text":"これはボタンです"},
                    "action_id": "button_click"
                }
            }
        ],
        text=f"Hello <@{message['user']}>!"
    )


@app.message("@GPT")
def ret_gpt(message, say):
    openai_client = OpenAI(api_key="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")
    slack_client = WebClient(token="xoxb-6234162450775-6250589504278-ZVMcjSF6g6xubqAQRgSIg9yp")
    message_text = message['text']
    message_channel = message['channel']
    message_thread_ts = message['ts']

    # ChatGPTへの問い合わせ
    chat_completion = openai_client.chat.completions.create(
        messages=[{"role": "user", "content": message_text}],
        model="gpt-4"
    )
    response_text = chat_completion.choices[0].message.content

    config = {
        'user': 'root',
        'password': 'hIxhon-9xinto-wernuf',
        'host': '34.135.69.97',
        'database': 'test1',
    }
    db_connection = mysql.connector.connect(**config)
    cursor = db_connection.cursor()
    text1 = message_text # 取得してきた質問
    vector1 = get_embedding(text1)
    # データベースから全てのベクトルを取得
    query = "SELECT content, vector, url, date FROM phese4;"
    cursor.execute(query)
    rows = cursor.fetchall()
    similarity_list = []
    for content, vector_bytes, url, date in rows:
        vector2 = pickle.loads(vector_bytes)
        similarity = cosine_similarity(vector1, vector2)
        similarity_list.append((similarity, content, url, date))
    # 類似度スコアでソートし、上位5つを取得
    similarity_list.sort(reverse=True)
    top_5_similar_texts = similarity_list[:5]
    # 結果を表示 
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
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
