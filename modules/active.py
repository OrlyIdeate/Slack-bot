from slack_bolt import App
from modules.chatgpt import chatgpt # chat-gptの回答を生成する関数
from modules.DB import execute_query # クエリを実行する関数

def active_start(thread_id, question, url, status="稼働中"):
    """スレッドのステータスを稼働中にする

    引数:
        thread_id (str): スレッドのID
        question (str): chat-gptへの質問
        url (str): メッセージ・スレッドのURL
        status (str, optional): 何も渡さなくていい. デフォルト値"稼働中".
    """
    answer = chatgpt(question) # chat-gptの回答を生成
    query = "INSERT INTO active_monitoring (thread_id, title, url, status) VALUES (%s, %s, %s, %s);" # データベースにデータを挿入するクエリ
    execute_query(query, (thread_id, answer, url, status)) # クエリ実行


def active_end(thread_id):
    """スレッドのステータスを終了にする

    引数:
        thread_id (str): スレッドのID
    """
    query = "UPDATE active_monitoring SET status = '終了' WHERE thread_id = %s;"
    execute_query(query, (thread_id))


def get_thread_info():
    """稼働中のスレッドを取得する

    Returns:
        list: 稼働中のスレッドの title, url が格納されたリスト
    """
    query = "SELECT title, url FROM active_monitoring WHERE status != '終了';"
    result= execute_query(query)
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

