from slack_bolt import App
from datetime import datetime
import pickle

from dotenv import load_dotenv
load_dotenv()

from modules.similarity import get_embedding
from modules.DB import execute_query

def source(app: App):
    @app.message("@upload")
    def data_stock(event, say):
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

        vector_bytes = pickle.dumps(get_embedding(content))
        today = datetime.now()
        say(f"Saving URL: {url}")

        # データベースにデータを挿入
        insert_query = "INSERT INTO phase4 (content, vector, url, date) VALUES (%s, %s, %s, %s);"
        execute_query(insert_query, (content, vector_bytes, url ,today))

        # 生成したURLをSlackチャンネルに返信
        say("保存しました。")

def upload(content, url, category):
    """DBにデータを保存します。

    引数:
        content (str): タイトル
        url (str): データのURL
        category (str): カテゴリ
    """
    vector = pickle.dumps(get_embedding(content)) # ベクトル化
    today = datetime.now() # 現在の日付
    insert_query = "INSERT INTO phase4 (content, vector, url, category, date) VALUES (%s, %s, %s, %s, %s);" # クエリ作成
    execute_query(insert_query, (content, vector, url, category, today)) # データベースにデータを挿入

def get_unique_categories():
    """DBのカテゴリからユニークな値を取得し返します。

    戻り値:
        list: カテゴリが格納されたリスト
    """
    categories = execute_query("SELECT DISTINCT category FROM phase4")

    # ここで None と "null" を除外
    filtered_categories = [category[0] for category in categories if category[0] is not None and category[0] != "null" and category[0] != "none"]

    if not filtered_categories:
        return ["カテゴリーがありません"]
    else:
        return filtered_categories

