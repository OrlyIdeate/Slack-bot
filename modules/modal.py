from slack_bolt import App

# .env読み込み
from dotenv import load_dotenv
load_dotenv()


from modules.chatgpt import chatgpt
from modules.similarity import get_top_5_similar_texts
from modules.show import db_list

def register_modal_handlers(app: App):
    @app.action("modal-shortcut")
    # Chat-GPTに質問するモーダル
    def open_modal(ack, body, client):
        ack()
        # モーダルを送信する
        modal_view = {
            "type": "modal",
            "callback_id": "modal-submit",
            "title": {"type": "plain_text", "text": "Chat-GPTに質問"},
            "submit": {"type": "plain_text", "text": "送信"},
            # 見た目の調整は https://app.slack.com/block-kit-builder を使うと便利です
            "blocks": [
                {
                    "type": "input",
                    "block_id": "question-block",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "input_field"
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "質問を入力してください"
                    }
                }
            ]
        }

        client.views_open(
            trigger_id=body["trigger_id"],
            view=modal_view
        )

    @app.view("modal-submit")
    def modal_submit(ack, body, client):
        ack()
        # フォーム（モーダル）で受け取った質問が入ってる変数
        question = body["view"]["state"]["values"]["question-block"]["input_field"]["value"]
        # 入力されたデータをチャンネルに送信する
        channel_id = "C067ALJLXRQ"  # メッセージを送信するチャンネルのIDに置き換えてください

        response_text = chatgpt(question)

        thread = client.chat_postMessage(
            channel=channel_id,
            text=f"受け取った質問: {question}"
        )

        client.chat_postMessage(
            channel=channel_id,
            thread_ts=thread['ts'],
            text=response_text
        )



    @app.action("open_search_modal")
    def open_search_modal(ack, body, client):
        ack()
        client.views_open(
            trigger_id=body["trigger_id"],
            view={
                "type": "modal",
                "callback_id": "search_modal",
                "title": {"type": "plain_text", "text": "検索"},
                "blocks": [
                    {
                        "type": "input",
                        "block_id": "search_query",
                        "label": {"type": "plain_text", "text": "検索クエリ"},
                        "element": {"type": "plain_text_input", "action_id": "input"}
                    }
                ],
                "submit": {"type": "plain_text", "text": "検索"}
            }
        )

    @app.view("search_modal")
    def handle_search_submission(ack, body, client, view):
        ack()
        search_query = view["state"]["values"]["search_query"]["input"]["value"]
        top_5_similar_texts = get_top_5_similar_texts(search_query)
        # 結果を表示
        response_text = "*検索結果*:\n\n"
        for _, content, url, date in top_5_similar_texts:
            response_text += f"*Content:* {content}\n"
            response_text += f"*URL:* <{url}|Link>\n"
            response_text += f"*Date:* {date}\n\n"
        client.chat_postMessage(
            channel=body["user"]["id"],
            text=response_text
        )


    @app.action("db_list")
    def open_modal(ack, body, client):
        ack()
        client.views_open(
            trigger_id=body["trigger_id"],
            view={
                "type": "modal",
                "title": {"type": "plain_text", "text": "全ナレッジ"},
                "blocks": [
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": db_list()[:400]},
                    }
                ],
            },
        )