from slack_bolt import App

# .env読み込み
from dotenv import load_dotenv
load_dotenv()

from slack_sdk.errors import SlackApiError
from modules.chatgpt import chatgpt
from modules.similarity import get_top_5_similar_texts
from modules.show import db_list
from modules.upload import upload, get_unique_categories
from modules.kit import kit_generate2
from modules.delete import del_message

def register_modal_handlers(app: App):
    @app.action("question")
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
        del_message(client, body)

    @app.view("modal-submit")
    def modal_submit(ack, body, client):
        ack()
        # フォーム（モーダル）で受け取った質問が入ってる変数
        question = body["view"]["state"]["values"]["question-block"]["input_field"]["value"]
        # 入力されたデータをチャンネルに送信する
        channel_id = "C067ALJLXRQ"  # メッセージを送信するチャンネルのIDに置き換えてください

        thread = client.chat_postMessage(
            channel=channel_id,
            text=f"受け取った質問: {question}"
        )
        notion=client.chat_postMessage(
            channel=channel_id,
            thread_ts=thread['ts'],
            text="生成しています。少々お待ちください..."
        )
        response_text = chatgpt(question)
        client.chat_delete(
            channel=channel_id,
            ts=notion['ts']
        )
        ruizi = kit_generate2()["blocks"]
        client.chat_postMessage(
            channel=channel_id,
            thread_ts=thread['ts'],
            blocks=response_text[0]["blocks"]
        )
        client.chat_postMessage(
            channel=channel_id,
            thread_ts=thread['ts'],
            blocks=ruizi
        )
        for i in range (5):
            client.chat_postMessage(
            channel=channel_id,
            thread_ts=thread['ts'],
            blocks=response_text[i+1]["blocks"]
        )



    @app.action("search")
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
        del_message(client, body)

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
        categories = get_unique_categories()

        category_options = [{"text": {"type": "plain_text", "text": "All"}, "value": "All"}]
        category_options.extend([
            {"text": {"type": "plain_text", "text": category}, "value": category}
            for category in categories
        ])


        try:
            client.views_open(
                trigger_id=body["trigger_id"],
                view={
                    "type": "modal",
                    "callback_id": "category_selection_modal",
                    "title": {"type": "plain_text", "text": "カテゴリー選択"},
                    "submit": {"type": "plain_text", "text": "送信"},
                    "blocks": [
                        {
                            "type": "input",
                            "block_id": "category_selection_block",
                            "element": {
                                "type": "static_select",
                                "placeholder": {"type": "plain_text", "text": "カテゴリーを選択してください"},
                                "options": category_options,
                                "action_id": "category_select"
                            },
                            "label": {"type": "plain_text", "text": "カテゴリー"}
                        }
                    ]
                }
            )
        except SlackApiError as e:
            print(f"Error opening modal: {e}")

        del_message(client, body)

    selected_categories = {}

    @app.view("category_selection_modal")
    def handle_category_selection(ack, body, client, view):
        ack()
        user_id = body["user"]["id"]  # ユーザーIDを取得
        selected_category = view["state"]["values"]["category_selection_block"]["category_select"]["selected_option"]["value"]
        selected_categories[user_id] = selected_category
        page_number = 0
        page_size = 5
        response_text = db_list(selected_category, page_number, page_size)

        new_modal_payload = {
            "type": "modal",
            "title": {"type": "plain_text", "text": "全ナレッジ"},
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": response_text},
                },
                # ページネーション用のボタンを追加
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "前へ"},
                            "action_id": "prev_page",
                            "value": str(page_number - 1)
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "次へ"},
                            "action_id": "next_page",
                            "value": str(page_number + 1)
                        }
                    ]
                },
            ],
        }

        # 新しいモーダルを開く
        try:
            response = client.views_open(
                trigger_id=body["trigger_id"],  # トリガーIDの使用
                view=new_modal_payload
            )
        except SlackApiError as e:
            print("Error opening new modal:", e.response["error"])



    @app.action("prev_page")
    @app.action("next_page")
    def handle_pagination_action(ack, body, client, action):
        ack()
        page_number = int(action["value"])
        page_size = 5
        user_id = body["user"]["id"]  # ユーザーIDを取得
        selected_category = selected_categories.get(user_id)
        if action["action_id"] == "next_page":
            page_number += 1
        elif action["action_id"] == "prev_page":
            page_number -= 1

        new_page_data = db_list(selected_category, page_number, page_size)

        # モーダルを新しいビューで更新
        try:
            client.views_update(
                view_id=body["view"]["id"],
                view={
                    "type": "modal",
                    "title": {"type": "plain_text", "text": "全ナレッジ"},
                    "blocks": [
                        {
                            "type": "section",
                            "text": {"type": "mrkdwn", "text": new_page_data},
                        },
                        # ページネーション用のボタンを追加
                        {
                            "type": "actions",
                            "elements": [
                                {
                                    "type": "button",
                                    "text": {"type": "plain_text", "text": "前へ"},
                                    "action_id": "prev_page",
                                    "value": str(page_number - 1)
                                },
                                {
                                    "type": "button",
                                    "text": {"type": "plain_text", "text": "次へ"},
                                    "action_id": "next_page",
                                    "value": str(page_number + 1)
                                }
                            ]
                        }
                    ],
                }
            )
        except SlackApiError as e:
            print(f"Error opening modal: {e}")


    @app.action("upload")
    def open_modal(ack, body, client):
        ack()
        categories = get_unique_categories()  # データベースからカテゴリーを取得

        category_options = [{
            "text": {"type": "plain_text", "text": category},
            "value": category
        } for category in categories]

        try:
            client.views_open(
                trigger_id=body["trigger_id"],
                view={
                    "type": "modal",
                    "callback_id": "modal-identifier",
                    "title": {"type": "plain_text", "text": "アップロード"},
                    "blocks": [
                        {
                            "type": "section",
                            "block_id": "category_selection_block",
                            "text": {"type": "mrkdwn", "text": "どのようなカテゴリーのものをアップロードしますか？"},
                            "accessory": {
                                "type": "radio_buttons",
                                "options": [
                                    {
                                        "text": {"type": "plain_text", "text": "登録されたカテゴリーを選ぶ"},
                                        "value": "choose_category"
                                    },
                                    {
                                        "text": {"type": "plain_text", "text": "新しくカテゴリーを入力する"},
                                        "value": "enter_category"
                                    }
                                ],
                                "action_id": "category_selection"
                            }
                        },
                        {
                            "type": "section",
                            "block_id": "registered_category_block",
                            "text": {"type": "mrkdwn", "text": "登録されているカテゴリー:"},
                            "accessory": {
                                "type": "static_select",
                                "placeholder": {
                                    "type": "plain_text",
                                    "text": "カテゴリーを選択"
                                },
                                "options": category_options,
                                "action_id": "registered_category_select"
                            }
                        }
                    ]
                }
            )
        except SlackApiError as e:
            print(f"Error updating modal: {e}")

        del_message(client, body)

    @app.action("category_selection")
    def handle_selection(ack, body, client):
        ack()
        categories = get_unique_categories()
        user_selection = body['actions'][0]['selected_option']['value']
        category_options = [{"text": {"type": "plain_text", "text": category}, "value": category} for category in categories]

        if user_selection == 'choose_category':
            # 「カテゴリーを選ぶ」が選択された場合の処理
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
                            {
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
                        ]
                    }
        else:
            # 「カテゴリーを入力する」が選択された場合の処理
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
                            {
                                "type": "input",
                                "block_id": "category-input-block",
                                "element": {
                                    "type": "plain_text_input",
                                    "action_id": "category_input",
                                    "placeholder": {"type": "plain_text", "text": "新しいカテゴリーを入力してください"},
                                },
                                "label": {"type": "plain_text", "text": "または新しいカテゴリーを入力"}
                            }

                        ]
                    }
        try:
            client.views_update(
                trigger_id=body["trigger_id"],
                view_id=body["view"]["id"], # 追加: 現在のモーダルビューID
                view=modal_view_up
            )
        except SlackApiError as e:
            print(f"Error updating modal: {e}")

    @app.view("modal-submit_up")  # モーダルのcallback_idに合わせて設定
    def handle_modal_submission(ack, body, client, view, logger):
        ack()

        # モーダルからの入力値を取得
        content = view["state"]["values"]["content-block"]["content_input"]["value"]
        url = view["state"]["values"]["url-block"]["url_input"]["value"]

        # 選択されたカテゴリーまたは入力されたカテゴリーを取得
        try:
            selected_category = view["state"]["values"]["category-select-block"]["category_select"]["selected_option"]["value"]
        except KeyError:
            selected_category = None

        try:
            input_category = view["state"]["values"]["category-input-block"]["category_input"]["value"]
        except KeyError:
            input_category = None

        # カテゴリーの決定ロジック
        category = input_category or selected_category

        # upload関数を呼び出してデータベースに保存
        upload(content, url, category)

        # 保存された内容とカテゴリーをユーザーに通知
        response_message = f"保存された内容は以下です:\n内容: {content}\nURL: <{url}|Link>\nカテゴリー: {category}"
        client.chat_postMessage(channel=body["user"]["id"], text=response_message)