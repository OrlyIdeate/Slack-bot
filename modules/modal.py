import json, pickle
from slack_bolt import App
from datetime import datetime

# .env読み込み
from dotenv import load_dotenv
load_dotenv()

from slack_sdk.errors import SlackApiError
from modules.chatgpt import chatgpt
from modules.similarity import get_top_5_similar_texts, get_embedding
from modules.show import db_list
from modules.upload import upload, get_unique_categories
from modules.delete import del_message
from modules.active import active_start
from modules.save import get_thread_title, get_thread_summary
from modules.DB import execute_query

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

        with open("json/response_question.json") as f:
            answer_view = json.load(f)["blocks"]

        answer_view[2]["elements"][0]["text"] = response_text

        client.chat_postMessage(
            channel=channel_id,
            thread_ts=thread['ts'],
            blocks=answer_view
        )

        with open("json/similarity_list.json") as f:
            similar_view = json.load(f)["blocks"]
        similar = get_top_5_similar_texts(question)
        for _, content, url, date, category in similar:
            similar_view.append({"type": "divider"})
            similar_view.append(
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"*<{url}|{content}>*"
                        }
                    ]
                }
            )
            similar_view.append(
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*カテゴリ:* \n {category}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*追加日:* \n {date}"
                        }
                    ]
                }
            )


        client.chat_postMessage(
            channel=channel_id,
            thread_ts=thread['ts'],
            blocks=similar_view
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

    # スレッドをDBに保存するためのモーダルを開くショートカット
    @app.message_shortcut("save")
    def select_save_modal(ack, body, client):
        ack()
        ch_id = body["channel"]["id"]
        thread_ts = body["message"]["thread_ts"]
        team_domain = body["team"]["domain"]

        with open("json/save_modal.json") as f:
            modal_view = json.load(f)

        modal_view["select"]["private_metadata"] = f"{ch_id},{thread_ts},_,{team_domain}"
        client.views_open(
            trigger_id=body["trigger_id"],
            view=modal_view["select"]
        )


    @app.action("self")
    def title_save_modal(ack, body, client, logger):
        ack()
        ch_id, thread_ts, _, team_domain = body["view"]["private_metadata"].split(",")

        with open("json/save_modal.json") as f:
            modal_view = json.load(f)["self"]
        modal_view["private_metadata"] = f"{ch_id},{thread_ts},self,{team_domain}"
        client.views_update(
            view_id=body.get("view").get("id"),
            hash=body.get("view").get("hash"),
            view=modal_view
        )

    @app.action("generate")
    def generate_title_modal(ack, body, client):
        ack()
        ch_id, thread_ts, _, team_domain = body["view"]["private_metadata"].split(",")
        with open("json/save_modal.json") as f:
            modal_view = json.load(f)
        modal_view["loading"]["private_metadata"] = f"{ch_id},{thread_ts},_,{team_domain}"

        # まず「処理中...」である旨を伝える
        client.views_update(
            view_id=body.get("view").get("id"),
            hash=body.get("view").get("hash"),
            view=modal_view["loading"]
        )

        title = get_thread_title(client, ch_id, thread_ts)
        modal_view["generate"]["blocks"][1]["text"]["text"] = f"```{title}```"
        modal_view["generate"]["private_metadata"] = f"{ch_id},{thread_ts},{title},{team_domain}"
        client.views_update(
            view_id=body.get("view").get("id"),
            view=modal_view["generate"]
        )

    @app.view("save_submit")
    def modal_submit(ack, body, client):
        with open("json/save_modal.json") as f:
            modal_view = json.load(f)
        ack(
            response_action="update",
            view=modal_view["end_loading"]
        )



        # フォーム（モーダル）で受け取った質問が入ってる変数
        ch_id, thread_ts, title, team_domain = body["view"]["private_metadata"].split(",")
        if title == "self":
            title = body["view"]["state"]["values"]["title"]["title_input"]["value"]

        # スレッドのURLを作成
        url = f"https://{team_domain}.slack.com/archives/{ch_id}/p{thread_ts}"

        date = datetime.now().date()
        vector = pickle.dumps(get_embedding(title))

        modal_view["end"]["blocks"][2]["elements"][0]["text"] = f"<{url}|{title}>"
        modal_view["end"]["blocks"][3]["fields"][0]["text"] += "スレッド"
        modal_view["end"]["blocks"][3]["fields"][1]["text"] += str(date)

        execute_query(f"INSERT INTO phese4 (content, vector, url, date, category) VALUES (%s, %s, %s, %s, %s);", (title, vector, url, date, "スレッド"))

        client.views_update(
            view_id=body.get("view").get("id"),
            view=modal_view["end"]
        )

        summary = get_thread_summary(client, ch_id, thread_ts)
        summary, question, conclusion = summary.split("\n\n")
        modal_view["post_summary"]["blocks"][1]["elements"][0]["text"] = question[3:]
        modal_view["post_summary"]["blocks"][4]["elements"][0]["text"] = summary[3:]
        modal_view["post_summary"]["blocks"][7]["elements"][0]["text"] = conclusion[3:]


        client.chat_postMessage(
            channel=ch_id,
            thread_ts=thread_ts,
            blocks=modal_view["post_summary"]["blocks"]
        )


