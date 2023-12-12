import os
from slack_bolt import App
from datetime import datetime
import mysql
import pickle

from dotenv import load_dotenv
load_dotenv()

from .similarity import get_embedding

def save(app: App):
    @app.message("@save")
    def handle_message(event, say):
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
