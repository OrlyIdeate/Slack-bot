import json
from slack_bolt import App
from datetime import datetime

# .env読み込み
from dotenv import load_dotenv
load_dotenv()

from slack_sdk.errors import SlackApiError
from modules.active import get_thread_info
from modules.chatgpt import chatgpt, stream_chat
from modules.DB import execute_query
from modules.similarity import get_top_5_similar_texts
from modules.show import db_list
from modules.upload import upload, get_unique_categories
from modules.delete import del_message
from modules.active import active_start, active_end
from modules.save import get_thread_title, get_thread_summary

def register_modal_handlers(app: App):
    @app.action("question")
    def open_modal(ack, body, client):
        ack()
        ch_id = body["channel"]["id"]
        ts = body["message"]["ts"]
        team_domain = body["team"]["domain"]
        # "question_view.json" からモーダルの定義を読み込む
        with open("json/question_view.json", "r") as file:
            modal_view = json.load(file)
        modal_view["question"]["private_metadata"] = f"{ch_id},{team_domain}"

        client.views_open(
            trigger_id=body["trigger_id"],
            view=modal_view["question"]
        )
        # del_message関数の実装内容に基づいて適宜修正
        del_message(ch_id, ts)


    @app.view("question-submit")
    def response_gpt(ack, body, view, client):

        with open("json/question_view.json", "r") as file:
            modal_view = json.load(file)

        ch_id, team_domain = view["private_metadata"].split(",")
        question = body["view"]["state"]["values"]["question-block"]["input_field"]["value"]
        # modal_view["answer"]["private_metadata"] = f"{ch_id},{team_domain},{question}"

        ack(
            response_action="update",
            view=modal_view["loading"]
        )

        ch_id, team_domain = view["private_metadata"].split(",")

        modal_view["answer"]["private_metadata"] = f"{ch_id},{team_domain},{question}"
        modal_view["answer"]["blocks"][0]["text"]["text"] = " "

        # ストリーミング形式
        # for response_gpt in stream_chat(question):
        #     modal_view["answer"]["blocks"][0]["text"]["text"] += response_gpt
        #     client.views_update(
        #         view_id=body.get("view").get("id"),
        #         view=modal_view["answer"]
        #     )

        # サイレント形式
        modal_view["answer"]["blocks"][0]["text"]["text"] = chatgpt(question)
        client.views_update(
            view_id=body.get("view").get("id"),
            view=modal_view["answer"]
        )



    @app.view_submission("answer-submit")
    def answer_submit(ack, body, view, client):
        ack()
        ch_id, team_domain, question = view["private_metadata"].split(",")
        # フォーム（モーダル）で受け取った質問が入ってる変数
        answer = body["view"]["blocks"][0]["text"]["text"]
        # 入力されたデータをチャンネルに送信する

        thread = client.chat_postMessage(
            channel=ch_id,
            text=f"{question}"
        )

        thread_ts=thread["ts"]

        # notion=client.chat_postMessage(
        #     channel=ch_id,
        #     thread_ts=thread_ts,
        #     text="生成しています。少々お待ちください..."
        # )
        # del_message(ch_id, notion["ts"])

        with open("json/response_question.json") as f:
            answer_view = json.load(f)["blocks"]

        answer_view[0]["text"]["text"] = answer

        client.chat_postMessage(
            channel=ch_id,
            thread_ts=thread_ts,
            text=answer,
            blocks=answer_view
        )

        with open("json/similarity_list.json") as f:
            similar_view = json.load(f)["blocks"]
        similar = get_top_5_similar_texts(question)
        for _, content, url, date, category in similar:
            similar_view[0]["text"]["text"] = f"*<{url}|{content}>*"
            similar_view[1]["elements"][0]["text"] = f":hash:{category}"
            similar_view[1]["elements"][1]["text"] = f":calendar:{date}"

            client.chat_postMessage(
                channel=ch_id,
                thread_ts=thread_ts,
                text="類似コンテンツ",
                blocks=similar_view
            )

        summary_prompt = question + "\n\nこの内容をタイトル風にして。"
        url = f"https://{team_domain}.slack.com/archives/{ch_id}/p{thread_ts}" # スレッドのURLを作成
        active_start(thread_ts , summary_prompt, url, "稼働中")



    @app.action("search")
    def open_search_modal(ack, body, client):
        ack()
        # JSONファイルからモーダルの定義を読み込む
        with open("json/search_view.json", "r") as file:
            search_view = json.load(file)

        client.views_open(
            trigger_id=body["trigger_id"],
            view=search_view
        )

        # del_message関数の実装内容に基づいて適宜修正
        del_message(body["channel"]["id"], body["message"]["ts"])

    @app.view("search_modal")
    def handle_search_submission(ack, body, client, view):
        ack()
        search_query = view["state"]["values"]["search_query"]["input"]["value"]
        top_5_similar_texts = get_top_5_similar_texts(search_query)
        # 結果を表示
        response_text = "*検索結果*:\n\n"
        for similarity, content, url, date, category in top_5_similar_texts:
            response_text += f"*内容:* <{url}|{content}>\n"
            response_text += f"*日付:* {date}\n"
            response_text += f"*カテゴリ:* {category}\n\n"
        client.chat_postMessage(
            channel=body["user"]["id"],
            text=response_text
        )


    @app.action("db_list")
    def open_db_list_first_modal(ack, body, client):
        ack()

        with open("json/list.json") as f:
            views = json.load(f)

        if execute_query("SELECT url FROM active_monitoring LIMIT 1;"):
            views["first_modal"]["blocks"].append(views["active_thread_modal"])

        client.views_open(
            trigger_id=body["trigger_id"],
            view=views["first_modal"]
        )

        del_message(body["channel"]["id"], body["message"]["ts"])

    @app.action("category_select")
    def category_select(ack, body, client):
        ack()
        category_options = []
        category_options.extend([
            {"text": {"type": "plain_text", "text": category}, "value": category}
            for category in get_unique_categories()
        ])

        try:
            with open("json/db_category_view.json", "r") as file:
                modal_view = json.load(file)

            # カテゴリのオプションを動的に追加
            modal_view["blocks"][0]["element"]["options"] = category_options

            client.views_update(
                view_id=body.get("view").get("id"),
                view=modal_view
            )
        except SlackApiError as e:
            print(f"Error opening modal: {e}")


    @app.action("selected_category")
    @app.view("selected_category")
    def handle_category_selection(ack, body, client, view):
        with open("json/list.json") as f:
            views = json.load(f)

        try:
            category = view["state"]["values"]["category_selection_block"]["category_select"]["selected_option"]["value"]
        except TypeError:
            category = "All"

        ack(
            response_action="update",
            view=views["loading_modal"]
        )

        page_number = 0
        page_size = 5
        response_text = db_list(category, page_number, page_size)

        # "db_page_view.json" からモーダルの定義を読み込む
        with open("json/db_page_view.json", "r") as file:
            views = json.load(file)

        # 動的なコンテンツを更新
        views["blocks"][0]["text"]["text"] = response_text
        views["blocks"][1]["elements"][0]["value"] = str(page_number - 1)
        views["blocks"][1]["elements"][1]["value"] = str(page_number + 1)
        views["private_metadata"] = category

        client.views_update(
            view_id=body.get("view").get("id"),
            view=views
        )



    @app.action("prev_page")
    @app.action("next_page")
    def handle_pagination_action(ack, body, client, view, action):
        ack()
        page_number = int(action["value"])
        page_size = 5
        category = body["view"]["private_metadata"]

        if action["action_id"] == "next_page":
            page_number += 1
        elif action["action_id"] == "prev_page":
            page_number -= 1

        new_page_data = db_list(category, page_number, page_size)

        # "db_move_view.json" からモーダルの定義を読み込む
        with open("json/db_move_view.json", "r") as file:
            views = json.load(file)

        # 動的なコンテンツを更新
        views["blocks"][0]["text"]["text"] = new_page_data
        views["blocks"][1]["elements"][0]["value"] = str(page_number - 1)
        views["blocks"][1]["elements"][1]["value"] = str(page_number + 1)
        views["private_metadata"] = category

        try:
            client.views_update(
                view_id=body["view"]["id"],
                view=views
            )
        except SlackApiError as e:
            print(f"Error opening modal: {e}")

    upload_timestamp = {}

    @app.action("upload")
    def open_modal(ack, body, client):
        ack()

        try:
            with open("json/upload_view.json", "r") as file:
                upload_view = json.load(file)

            client.views_open(
                trigger_id=body["trigger_id"],
                view=upload_view
            )

        except SlackApiError as e:
            print(f"Error updating modal: {e}")

        ch_id = body["channel"]["id"]
        ts = body["message"]["ts"]

        # del_message関数の実装内容に基づいて適宜修正
        del_message(ch_id, ts)

    @app.message_shortcut("upload_thread")
    def open_modal(ack, body, client):
        ack()
        user_id = body["user"]["id"]
        message_ts = body["message"]["ts"]

        # スレッドのタイムスタンプを辞書に格納
        # これでスレッドにアップロードをするかどうかを制御します。
        upload_timestamp[user_id] = message_ts
        try:
            with open("json/upload_view.json", "r") as file:
                upload_view = json.load(file)

            client.views_open(
                trigger_id=body["trigger_id"],
                view=upload_view
            )

        except SlackApiError as e:
            print(f"Error updating modal: {e}")

    @app.action("category_selection")
    def handle_selection(ack, body, client):
        ack()
        categories = get_unique_categories()
        user_selection = body["actions"][0]["selected_option"]["value"]
        category_options = [{"text": {"type": "plain_text", "text": category}, "value": category} for category in categories]

        if user_selection == "choose_category":
            # JSONファイルからモーダルの定義を読み込む
            with open("json/upload_selection_view.json", "r") as file:
                modal_view_up = json.load(file)

            # カテゴリーオプションを動的に追加
            modal_view_up["blocks"][2]["element"]["options"] = category_options
        else:
            # JSONファイルからモーダルの定義を読み込む
            with open("json/upload_input_view.json", "r") as file:
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
        ack(
            response_action="update",
            view={
                "type": "modal",
                "title": {
                    "type": "plain_text",
                    "text": "アップロード"
                },
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "読込中…"
                        }
                    }
                ]
            }
        )

        # モーダルからの入力値を取得
        selected_option = view["state"]["values"]["radio_buttons"]["radio_buttons_action"]["selected_option"]["value"]

        categories = get_unique_categories()
        category_options = [{"text": {"type": "plain_text", "text": category}, "value": category} for category in categories]

        if selected_option == "choose_category":
            # JSONファイルからモーダルの定義を読み込む
            with open("json/upload_selection_view.json", "r") as file:
                modal_view_up = json.load(file)

            # カテゴリーオプションを動的に追加
            modal_view_up["blocks"][2]["element"]["options"] = category_options
        else:
            # JSONファイルからモーダルの定義を読み込む
            with open("json/upload_input_view.json", "r") as file:
                modal_view_up = json.load(file)

        try:
            client.views_update(
                trigger_id=body["trigger_id"],
                view_id=body["view"]["id"],
                view=modal_view_up
            )
        except SlackApiError as e:
            print(f"Error updating modal: {e}")

    @app.view("uploading")
    def uploading(ack, view, client, body):
        ack(
            response_action="update",
            view={
                "type": "modal",
                "title": {
                    "type": "plain_text",
                    "text": "アップロード"
                },
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "保存しました"
                        }
                    }
                ]
            }
        )
        content = view["state"]["values"]["content-block"]["plain_text_input-action"]["value"]
        url = view["state"]["values"]["url-block"]["url_input"]["value"]
        # 選択されたカテゴリーまたは入力されたカテゴリーを取得
        try:
            selected_option = view["state"]["values"]["category-select-block"]["category_select"].get("selected_option")
            selected_category = selected_option["value"] if selected_option else None
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
        response_message = f"保存された内容は以下です:\n内容: <{url}|{content}>\nカテゴリ: {category}"
        client.chat_postMessage(channel=body["user"]["id"], text = response_message)

        with open("json/response_message_block.json", "r") as file:
            message_block = json.load(file)

        # プレースホルダーを実際の値で置き換え
        for block in message_block["blocks"]:
            if block["type"] == "context":
                for element in block["elements"]:
                    element["text"] = element["text"].replace("URL_PLACEHOLDER", url).replace("CONTENT_PLACEHOLDER", content).replace("CATEGORY_PLACEHOLDER", category)

        user_id = body["user"]["id"]
        if user_id in upload_timestamp and upload_timestamp[user_id]:
            thread_ts = upload_timestamp[user_id]
            client.chat_postMessage(
                channel="C067ALJLXRQ",
                blocks=message_block["blocks"],
                thread_ts=thread_ts
            )
        if user_id in upload_timestamp:
            del upload_timestamp[user_id]









    # タイトルの設定方法を選択
    @app.message_shortcut("save")
    def select_save_modal(ack, body, client):
        ack()
        ch_id = body["channel"]["id"] # ch_id取得
        thread_ts = body["message"]["thread_ts"] # thread_ts取得
        team_domain = body["team"]["domain"] # team_domain取得

        with open("json/save_modal.json") as f:
            modal_view = json.load(f) # jsonからmodal_view読込

        modal_view["first"]["private_metadata"] = f"{ch_id},{thread_ts},{team_domain}" # private_metadataを追加

        # モーダルを起動
        client.views_open(
            trigger_id=body["trigger_id"],
            view=modal_view["first"]
        )

    # スレッドタイトル自動生成
    @app.action("generate")
    def generate_title_modal(ack, body, client):
        ack()
        ch_id, thread_ts, team_domain = body["view"]["private_metadata"].split(",") # private_metadata取得

        # json読込
        with open("json/save_modal.json") as f:
            modal_view = json.load(f)

        modal_view["loading"]["private_metadata"] = f"{ch_id},{thread_ts},{team_domain}" # private_metadata追加

        # 「生成中...」モーダル起動
        client.views_update(
            view_id=body.get("view").get("id"),
            hash=body.get("view").get("hash"),
            view=modal_view["loading"]
        )

        title = get_thread_title(client, ch_id, thread_ts) # タイトル生成

        modal_view["generate"]["blocks"][0]["element"]["initial_value"] = f"{title}" # 生成したタイトルをビューに設定
        modal_view["generate"]["private_metadata"] = f"{ch_id},{thread_ts},{team_domain}" # private_metadata追加

        # 「生成したタイトル」モーダル起動
        client.views_update(
            view_id=body.get("view").get("id"),
            view=modal_view["generate"]
        )

    # スレッド保存
    @app.view("save_submit")
    def modal_submit(ack, body, client):

        # json読込
        with open("json/save_modal.json") as f:
            modal_view = json.load(f)

        # 「保存中...」モーダル起動
        ack(
            response_action="update",
            view=modal_view["end_loading"]
        )

        ch_id, thread_ts, team_domain = body["view"]["private_metadata"].split(",") # private_metadata取得

        title = body["view"]["state"]["values"]["title_input"]["title"]["value"] # 入力されたタイトル取得

        # スレッドのURLを作成
        url = f"https://{team_domain}.slack.com/archives/{ch_id}/p{thread_ts}"

        date = datetime.now().date() # 現在日取得

        # 保存した内容を表示するモーダルビュー作成
        modal_view["end"]["blocks"][2]["text"]["text"] = f"*<{url}|{title}>*"
        modal_view["end"]["blocks"][3]["fields"][0]["text"] += "スレッド"
        modal_view["end"]["blocks"][3]["fields"][1]["text"] += str(date)

        # 保存した内容を表示するモーダル起動
        client.views_update(
            view_id=body.get("view").get("id"),
            view=modal_view["end"]
        )

        upload(title, url, "スレッド") # DBにアップロード
        active_end(url) # スレッドの稼働状況を「停止」に上書き

        summary = get_thread_summary(client, ch_id, thread_ts) # スレッド内の要約を生成
        question = summary[1]
        conclusion = summary[2]
        summary=summary[0]

        # block_kitを作成
        modal_view["post_summary"]["blocks"][1]["elements"][0]["text"] = question
        modal_view["post_summary"]["blocks"][4]["elements"][0]["text"] = summary
        modal_view["post_summary"]["blocks"][7]["elements"][0]["text"] = conclusion

        # スレッドに要約を投稿
        client.chat_postMessage(
            channel=ch_id,
            thread_ts=thread_ts,
            text=f"{question}\n{summary}\n{conclusion}",
            blocks=modal_view["post_summary"]["blocks"]
        )


    @app.action("active_thread")
    def thread_monitor_modal(ack, body, client):
        ack()
        active_threads = get_thread_info()

        # JSONファイルを読み込む
        with open("json/active_thread_list.json", "r") as file:
            modal_view = json.load(file)

        # 稼働中のスレッドの情報をブロックに追加
        for title, url in active_threads:
            thread_block = {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*<{url}|{title}>*"
                }
            }
            modal_view["blocks"].append(thread_block)
            modal_view["blocks"].append({"type": "divider"})

        # モーダルを表示
        client.views_update(
                view_id=body.get("view").get("id"),
                view=modal_view
            )
