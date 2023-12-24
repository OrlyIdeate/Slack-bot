import logging
logging.basicConfig(level=logging.ERROR)

import os
from slack_bolt import App
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import mysql.connector

from dotenv import load_dotenv
load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")


def db_list():

    """DBから全情報を取得します。
    """

    config = {
        'user': 'root',
        'password': 'citson-buzrit-4cyxZu',
        'host': '35.223.243.48',
        'database': 'test1',
        }
    db_connection = mysql.connector.connect(**config)
    cursor = db_connection.cursor()
    query = "SELECT content, url, date FROM phese4;"
    cursor.execute(query)
    rows = cursor.fetchall()

    similarity_list = []
    for content, url, date in rows:
        similarity_list.append((content, url, date))
    response_text = "*保存されているデータ*:\n\n"

    for content, url, date in similarity_list:
        response_text += f"*Content:* {content}\n"
        response_text += f"*URL:* <{url}|Link>\n"
        response_text += f"*Date:* {date}\n\n"
    return response_text


def select_all_db(app: App):
    @app.message("@show")
    def get_db_data(message, say):
        slack_client = WebClient(token=SLACK_BOT_TOKEN)
        message_channel = message['channel']
        message_thread_ts = message['ts']


        response_text = db_list() # phese4テーブルから全情報を取得する

        try:
        # スレッド内に返信を送信
            response = slack_client.chat_postMessage(
                channel=message_channel,
                text=response_text,
                thread_ts=message_thread_ts
            )
        except SlackApiError as e:
            print(f"Error sending message: {e.response['error']}")