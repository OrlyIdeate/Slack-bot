import os
from slack_bolt import App
from slack_sdk.web import WebClient
import mysql.connector
import openai

from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

def active_start(thread_id, question, url, status):
    openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
    # データベース接続設定
    config = {
        'user': 'root',
        'password': 'citson-buzrit-4cyxZu',
        'host': '35.223.243.48',
        'database': 'test1',
        }
    db_connection = mysql.connector.connect(**config)
    cursor = db_connection.cursor()

    summary_completion = openai_client.chat.completions.create(
        messages=[{"role": "user", "content": question}],
        model="gpt-4"
    )
    summary_text = summary_completion.choices[0].message.content

    # データベースにデータを挿入するクエリ
    insert_query = """
    INSERT INTO active_monitoring (thread_id, title, url, status)
    VALUES (%s, %s, %s, %s)
    """
    cursor.execute(insert_query, (thread_id, summary_text, url, status))
    db_connection.commit()
    cursor.close()
    db_connection.close()

def active_end(thread_id):
    # データベース接続設定
    config = {
        'user': 'root',
        'password': 'citson-buzrit-4cyxZu',
        'host': '35.223.243.48',
        'database': 'test1',
        }
    db_connection = mysql.connector.connect(**config)
    cursor = db_connection.cursor()

    update_query = """
    UPDATE active_monitoring
    SET status = '終了'
    WHERE thread_id = %s
    """
    cursor.execute(update_query, (thread_id,))
    db_connection.commit()
    cursor.close()
    db_connection.close()

def get_thread_info():
    # データベース接続設定
    config = {
        'user': 'root',
        'password': 'citson-buzrit-4cyxZu',
        'host': '35.223.243.48',
        'database': 'test1',
        }
    db_connection = mysql.connector.connect(**config)
    cursor = db_connection.cursor()

    # スレッド情報を取得するクエリ
    query = """
    SELECT title, url
    FROM active_monitoring
    WHERE status != '終了'
    """
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    db_connection.close()
    return result

def thread_monitor(app: App):
    @app.message("@thread")
    def handle_thread_command(event, say):
        # データベースから稼働中のスレッド情報を取得
        thread_infos = get_thread_info()
        if thread_infos:
            response_text = "*稼働中のスレッド一覧*:\n\n"
            for title, url in thread_infos:
                response_text += f"*タイトル:* {title}\n"
                response_text += f"*URL:* <{url}|Link>\n\n"
            say(response_text)
        else:
            say("スレッドは全て終了しています。")

