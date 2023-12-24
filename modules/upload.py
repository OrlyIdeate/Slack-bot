import logging
logging.basicConfig(level=logging.ERROR)

import os
from slack_bolt import App
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from datetime import datetime
import mysql.connector
import pickle

from dotenv import load_dotenv
load_dotenv()

from modules.similarity import get_embedding

def source(app: App):
    @app.message("@upload")
    def data_stock(event, say):
        channel_id = event['channel']
        message_ts = event['ts']
        message_text = event['text']
        
        content = ""
        url = ""
        try:
            content_start = message_text.index("content=") + 8
            content_end = message_text.index(" url=", content_start)
            content = message_text[content_start:content_end].strip().strip('“”')

            url_start = message_text.index("url=", content_end) + 4
            url_end = message_text.index(" ", url_start) if " " in message_text[url_start:] else len(message_text)
            url = message_text[url_start:url_end].strip('"')
        except ValueError:
            # 適切な形式でない場合はエラーメッセージを送信
            say("メッセージの形式が正しくありません。")
            return

        config = {
            'user': 'root',
            'password': 'citson-buzrit-4cyxZu',
            'host': '35.223.243.48',
            'database': 'test1',
        }
        db_connection = mysql.connector.connect(**config)
        cursor = db_connection.cursor()
        text1 = content
        vector1 = get_embedding(text1)
        vector_bytes = pickle.dumps(vector1)

        today = datetime.now()
        say(f"Saving URL: {url}")

        # データベースにデータを挿入
        insert_query = "INSERT INTO phese4 (content, vector, url, date) VALUES (%s, %s, %s, %s);"
        cursor.execute(insert_query, (text1, vector_bytes, url ,today))
        db_connection.commit()

        # 生成したURLをSlackチャンネルに返信
        say("保存しました。")

def upload(content, url, category):
    config = {
        'user': 'root',
        'password': 'citson-buzrit-4cyxZu',
        'host': '35.223.243.48',
        'database': 'test1',
    }

    try:
        db_connection = mysql.connector.connect(**config)
        cursor = db_connection.cursor()

        # ベクトル化
        vector = get_embedding(content)
        vector_bytes = pickle.dumps(vector)

        # 現在の日付
        today = datetime.now()

        # データベースにデータを挿入
        insert_query = "INSERT INTO phese4 (content, vector, url, category, date) VALUES (%s, %s, %s, %s, %s);"
        cursor.execute(insert_query, (content, vector_bytes, url, category, today))
        db_connection.commit()

    except mysql.connector.Error as err:
        print("Database error: ", err)
    finally:
        if db_connection.is_connected():
            cursor.close()
            db_connection.close()

def get_unique_categories():
    config = {
        'user': 'root',
        'password': 'citson-buzrit-4cyxZu',
        'host': '35.223.243.48',
        'database': 'test1',
    }
    db_connection = mysql.connector.connect(**config)
    cursor = db_connection.cursor()
    cursor.execute("SELECT DISTINCT category FROM phese4")
    categories = cursor.fetchall()
    cursor.close()
    db_connection.close()

    # ここで None と "null" を除外
    filtered_categories = [category[0] for category in categories if category[0] is not None and category[0] != "null" and category[0] != "none"]

    if not filtered_categories:
        return ["カテゴリーがありません"]
    else:
        return filtered_categories

