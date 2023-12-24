from slack_bolt import App

# .env読み込み
from dotenv import load_dotenv
load_dotenv()


from modules.chatgpt import chatgpt
from modules.similarity import get_top_5_similar_texts
from modules.show import db_list
from modules.upload import upload, get_unique_categories
from modules.delete import del_message

def register_modal_handlers(app: App):
    @app.action("question")
    # Chat-GPTに質問するモーダル
    def open_modal(ack, body, client):
        ack()
        # モーダルを送信する
        modal_view = {
            "type": "modal",
            "callback_id": "send_question",
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

        del_message(client, body)

    @app.view("send_question")
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



    @app.action("search")
    def open_search_modal(ack, body, client):
        ack()
        client.views_open(
            trigger_id=body["trigger_id"],
            view={
                "type": "modal",
                "callback_id": "searching",
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

        del_message(client, body)

    @app.view("searching")
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
        del_message(client, body)


    @app.action("upload")
    def open_modal(ack, body, client):
        ack()
        del_message(client, body)
        categories = get_unique_categories()  # データベースからカテゴリーを取得

        if categories == ["カテゴリーがありません"]:
            # カテゴリー入力フィールドを定義
            category_block = {
                "type": "input",
                "block_id": "category-block",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "category_input",
                    "placeholder": {"type": "plain_text", "text": "新しいカテゴリーを入力してください"},
                    "initial_value": "null"
                },
                "label": {"type": "plain_text", "text": "カテゴリー"}
            }
            modal_view_up = {
                        "type": "modal",
                        "callback_id": "modal-submit_up",
                        "title": {"type": "plain_text", "text": "情報を入力"},
                        "submit": {"type": "plain_text", "text": "送信"},
                        "blocks": [
                            {
                                "type": "input",
                                "block_id": "content-block",
                                "element": {
                                    "type": "plain_text_input",
                                    "action_id": "content_input",
                                    "multiline": True
                                },
                                "label": {"type": "plain_text", "text": "内容を入力してください"}
                            },
                            {
                                "type": "input",
                                "block_id": "url-block",
                                "element": {
                                    "type": "plain_text_input",
                                    "action_id": "url_input"
                                },
                                "label": {"type": "plain_text", "text": "URLを入力してください"}
                            },
                            category_block  # カテゴリーブロックを追加
                        ]
                    }

        else:
            category_options = [{"text": {"type": "plain_text", "text": category}, "value": category} for category in categories]
            category_options.insert(0, {"text": {"type": "plain_text", "text": "null"}, "value": "none"})
            category_select_block = {
                "type": "input",
                "block_id": "category-select-block",
                "element": {
                    "type": "static_select",
                    "action_id": "category_select",
                    "placeholder": {"type": "plain_text", "text": "カテゴリーを選択してください"},
                    "options": category_options
                },
                "label": {"type": "plain_text", "text": "カテゴリーを選択"}
            }

            # カテゴリー入力フィールドを定義
            category_input_block = {
                "type": "input",
                "block_id": "category-input-block",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "category_input",
                    "placeholder": {"type": "plain_text", "text": "新しいカテゴリーを入力してください"},
                    "initial_value": "null"
                },
                "label": {"type": "plain_text", "text": "または新しいカテゴリーを入力"}
            }

            # モーダルビューを構築
            modal_view_up = {
                        "type": "modal",
                        "callback_id": "modal-submit_up",
                        "title": {"type": "plain_text", "text": "情報を入力"},
                        "submit": {"type": "plain_text", "text": "送信"},
                        "blocks": [
                            {
                                "type": "input",
                                "block_id": "content-block",
                                "element": {
                                    "type": "plain_text_input",
                                    "action_id": "content_input",
                                    "multiline": True
                                },
                                "label": {"type": "plain_text", "text": "内容を入力してください"}
                            },
                            {
                                "type": "input",
                                "block_id": "url-block",
                                "element": {
                                    "type": "plain_text_input",
                                    "action_id": "url_input"
                                },
                                "label": {"type": "plain_text", "text": "URLを入力してください"}
                            },
                            category_select_block,
                            category_input_block # カテゴリーブロックを追加
                        ]
                    }

        client.views_open(
            trigger_id=body["trigger_id"],
            view=modal_view_up
        )

    @app.view("modal-submit_up")  # モーダルのcallback_idに合わせて設定
    def handle_modal_submission(ack, body, client, view, logger):
        ack()

        print(view)

        # モーダルからの入力値を取得
        content = view["state"]["values"]["content-block"]["content_input"]["value"]
        url = view["state"]["values"]["url-block"]["url_input"]["value"]
        selected_category = view["state"]["values"]["category-select-block"]["category_select"]["selected_option"]["value"]

        # category-input-block から入力された値を取得
        input_category = view["state"]["values"]["category-input-block"]["category_input"]["value"]

        # カテゴリーの決定ロジック
        if input_category != "null":
            category = input_category
        else:
            category = selected_category

        # upload関数を呼び出してデータベースに保存
        upload(content, url, category)

        # 保存された内容とカテゴリーをユーザーに通知
        response_message = f"保存された内容は以下です:\n内容: {content}\nカテゴリー: {category}"
        client.chat_postMessage(channel=body["user"]["id"], text=response_message)
