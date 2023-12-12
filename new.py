import os
import pandas as pd
import pickle
import openai
import mysql.connector
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from slack_bolt import App
from slack_sdk.web import WebClient 
from slack_bolt.adapter.socket_mode import SocketModeHandler
from datetime import datetime
from modules.modal import register_modal_handlers # Slackのフォームの処理

# .envから環境変数を読み込む
load_dotenv()

# ボットトークンとソケットモードハンドラーを使ってアプリを初期化します
app = App(token=os.getenv("SLACK_BOT_TOKEN"))

register_modal_handlers(app) # Slackのフォームの処理

####################################################################################################

client = openai.OpenAI(
    # defaults to os.environ.get(“OPENAI_API_KEY”)
    api_key=os.getenv("OPENAI_API_KEY")
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

@app.message("@GPT")
def ret_gpt(message, say):
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    slack_client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
    message_text = message['text']
    message_channel = message['channel']
    message_thread_ts = message['ts']

    # ChatGPTへの問い合わせ
    message_text_with_instruction = message_text + " これは質問として十分ですか？不十分ですか？十分のときは十分の確認は必要なく、質問の回答だけを表示してください。不十分であれば回答はせずに何が不十分なのかを教えてください。"
    chat_completion = openai_client.chat.completions.create(
        messages=[{"role": "user", "content": message_text_with_instruction}],
        model="gpt-4"
    )
    response_text = chat_completion.choices[0].message.content

    if "この質問は不十分です" not in response_text:

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
                response_text += f"*Content:* {content}\n"
                response_text += f"*URL:* <{url}|Link>\n"
                response_text += f"*Date:* {date}\n\n"
                response_text += "-----------------------------\n"  # 区切り線を追加
    # スレッド内に返信を送信
    response = slack_client.chat_postMessage(
        channel=message_channel,
        text=response_text,
        thread_ts=message_thread_ts
    )


@app.message("@search")
def ret_gpt(message, say):
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    slack_client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
    message_text = message['text']
    message_channel = message['channel']
    message_thread_ts = message['ts']

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


@app.message("@show")
def ret_gpt(message, say):
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    slack_client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
    message_text = message['text']
    message_channel = message['channel']
    message_thread_ts = message['ts']
    config = {
        'user': 'root',
        'password': 'hIxhon-9xinto-wernuf',
        'host': '34.135.69.97',
        'database': 'test1',
    }
    db_connection = mysql.connector.connect(**config)
    cursor = db_connection.cursor()
    query = "SELECT content, url, date FROM phese4;"
    cursor.execute(query)
    rows = cursor.fetchall()

    similarity_list = []
    for content, url, date in rows:
        # 以前はここでvectorを処理していましたが、今は不要なので削除
        similarity_list.append((content, url, date))
    response_text = "*保存されているデータ*:\n\n"

    for content, url, date in similarity_list:
        response_text += f"*Content:* {content}\n"
        response_text += f"*URL:* <{url}|Link>\n"
        response_text += f"*Date:* {date}\n\n"
    # スレッド内に返信を送信
    response = slack_client.chat_postMessage(
        channel=message_channel,
        text=response_text,
        thread_ts=message_thread_ts
    )



@app.message("@save")
def handle_message(event, say):
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    slack_client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
    channel_id = event['channel']
    message_ts = event['ts']
    message_text = event['text']
    thread_ts = event.get('thread_ts', message_ts)  # スレッドのタイムスタンプを取得、なければメッセージのタイムスタンプを使用

    # スレッドのURLを生成
    thread_url = f"https://dec-ph4-hq.slack.com/archives/{channel_id}/p{message_ts.replace('.', '')}?thread_ts={thread_ts.replace('.', '')}&cid={channel_id}"

    config = {
        'user': 'root',
        'password': 'hIxhon-9xinto-wernuf',
        'host': '34.135.69.97',
        'database': 'test1',
    }
    db_connection = mysql.connector.connect(**config)
    cursor = db_connection.cursor()
    text1 = message_text # 取得してきた質問
    text1 = text1[6:] # @save の部分を消す
    vector1 = get_embedding(text1)
    vector_bytes = pickle.dumps(vector1)

    url = thread_url

    today = datetime.now()

    # データベースにデータを挿入
    insert_query = "INSERT INTO phese4 (content, vector, url, date) VALUES (%s, %s, %s, %s);"
    cursor.execute(insert_query, (text1, vector_bytes, url ,today))
    db_connection.commit()

    # 生成したURLをSlackチャンネルに返信
    say(text=f"スレッドのURL: {thread_url}", channel=channel_id)
    say("保存しました。")



# 上までで処理できなかった場合の例外処理
@app.event("message")
def handle_unhandled_message_events(event, logger):
    logger.info(f"未処理のメッセージイベント: {event}")

###########################################################################################

# アプリを起動します
if __name__ == "__main__":
    SocketModeHandler(app, os.getenv("SLACK_APP_TOKEN")).start()

