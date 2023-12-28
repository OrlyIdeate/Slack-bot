import logging
logging.basicConfig(level=logging.ERROR)

import os
from slack_bolt import App
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from modules.DB import connect_to_db

from dotenv import load_dotenv
load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")


def db_list(category, page_number, page_size):
    db_connection = connect_to_db()
    cursor = db_connection.cursor()

    # クエリの作成
    query = """
    SELECT content, url, date, category FROM phase4
    WHERE category = %s OR %s = 'All'
    ORDER BY date DESC
    """
    cursor.execute(query, (category, category))

    rows = cursor.fetchall()
    cursor.close()
    db_connection.close()

    # ページネーションの処理
    start_index = page_number * page_size
    end_index = start_index + page_size
    paginated_data = rows[start_index:end_index]

    # 結果のフォーマット
    response_text = "*保存されているデータ*:\n\n"
    for content, url, date, category in paginated_data:
        category_display = category if category else "なし"
        response_text += f"*Content:* {content}\n"
        response_text += f"*URL:* <{url}|Link>\n"
        response_text += f"*Date:* {date}\n"
        response_text += f"*Category:* {category_display}\n\n"

    return response_text


def select_all_db(app: App):
    @app.message("@show")
    def get_db_data(message, say):
        slack_client = WebClient(token=SLACK_BOT_TOKEN)
        message_channel = message['channel']
        message_thread_ts = message['ts']


        response_text = db_list() # phase4テーブルから全情報を取得する

        try:
        # スレッド内に返信を送信
            response = slack_client.chat_postMessage(
                channel=message_channel,
                text=response_text,
                thread_ts=message_thread_ts
            )
        except SlackApiError as e:
            print(f"Error sending message: {e.response['error']}")