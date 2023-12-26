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
from modules.active import active_start
import json

def register_modal_handlers(app: App):
    @app.action("question")
    def open_modal(ack, body, client):
        ack()
        # 'question_view.json' からモーダルの定義を読み込む
        with open('json/question_view.json', 'r') as file:
            modal_view = json.load(file)

        client.views_open(
            trigger_id=body["trigger_id"],
            view=modal_view
        )
        # del_message関数の実装内容に基づいて適宜修正
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
        summary_prompt = question + "\n\nこの内容をタイトル風にして。"
        thread_id = thread['ts']  # スレッドIDを取得
        thread_url = f"https://dec-ph4-hq.slack.com/archives/{channel_id}/p{thread_id.replace('.', '')}?thread_ts={thread_id.replace('.', '')}&cid={channel_id}"
        active_start(thread_id, summary_prompt, thread_url, "稼働中")



    @app.action("search")
    def open_search_modal(ack, body, client):
        ack()
        # JSONファイルからモーダルの定義を読み込む
        with open('json/search_view.json', 'r') as file:
            search_view = json.load(file)

        client.views_open(
            trigger_id=body["trigger_id"],
            view=search_view
        )
        # del_message関数の実装内容に基づいて適宜修正
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
            with open('json/db_category_view.json', 'r') as file:
                modal_view = json.load(file)

            # カテゴリのオプションを動的に追加
            modal_view["blocks"][0]["element"]["options"] = category_options

            client.views_open(
                trigger_id=body["trigger_id"],
                view=modal_view
            )
        except SlackApiError as e:
            print(f"Error opening modal: {e}")

        # del_message関数の実装内容に基づいて適宜修正
        del_message(client, body)

    selected_categories = {}

    @app.view("category_selection_modal")
    def handle_category_selection(ack, body, client, view):
        ack()
        user_id = body["user"]["id"]
        selected_category = view["state"]["values"]["category_selection_block"]["category_select"]["selected_option"]["value"]
        selected_categories[user_id] = selected_category
        page_number = 0
        page_size = 5
        response_text = db_list(selected_category, page_number, page_size)

        # 'db_page_view.json' からモーダルの定義を読み込む
        with open('json/db_page_view.json', 'r') as file:
            new_modal_payload = json.load(file)

        # 動的なコンテンツを更新
        new_modal_payload["blocks"][0]["text"]["text"] = response_text
        new_modal_payload["blocks"][1]["elements"][0]["value"] = str(page_number - 1)
        new_modal_payload["blocks"][1]["elements"][1]["value"] = str(page_number + 1)

        try:
            response = client.views_open(
                trigger_id=body["trigger_id"],
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
        user_id = body["user"]["id"]
        selected_category = selected_categories.get(user_id)

        if action["action_id"] == "next_page":
            page_number += 1
        elif action["action_id"] == "prev_page":
            page_number -= 1

        new_page_data = db_list(selected_category, page_number, page_size)

        # 'db_move_view.json' からモーダルの定義を読み込む
        with open('json/db_move_view.json', 'r') as file:
            new_modal_payload = json.load(file)

        # 動的なコンテンツを更新
        new_modal_payload["blocks"][0]["text"]["text"] = new_page_data
        new_modal_payload["blocks"][1]["elements"][0]["value"] = str(page_number - 1)
        new_modal_payload["blocks"][1]["elements"][1]["value"] = str(page_number + 1)

        try:
            client.views_update(
                view_id=body["view"]["id"],
                view=new_modal_payload
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
            with open('json/upload_view.json', 'r') as file:
                upload_view = json.load(file)

            # カテゴリーオプションを動的に追加
            upload_view["blocks"][1]["accessory"]["options"] = category_options

            client.views_open(
                trigger_id=body["trigger_id"],
                view=upload_view
            )
        except SlackApiError as e:
            print(f"Error updating modal: {e}")

        # del_message関数の実装内容に基づいて適宜修正
        del_message(client, body)

    @app.action("category_selection")
    def handle_selection(ack, body, client):
        ack()
        categories = get_unique_categories()
        user_selection = body['actions'][0]['selected_option']['value']
        category_options = [{"text": {"type": "plain_text", "text": category}, "value": category} for category in categories]

        if user_selection == 'choose_category':
            # JSONファイルからモーダルの定義を読み込む
            with open('json/upload_selection_view.json', 'r') as file:
                modal_view_up = json.load(file)

            # カテゴリーオプションを動的に追加
            modal_view_up["blocks"][2]["element"]["options"] = category_options
        else:
            # JSONファイルからモーダルの定義を読み込む
            with open('json/upload_input_view.json', 'r') as file:
                modal_view_up = json.load(file)

        try:
            client.views_update(
                trigger_id=body["trigger_id"],
                view_id=body["view"]["id"],
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