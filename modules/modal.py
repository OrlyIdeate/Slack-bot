import json
from slack_bolt import App
from datetime import datetime

# .env読み込み
from dotenv import load_dotenv
load_dotenv()

from slack_sdk.errors import SlackApiError
from modules.active import get_thread_info
from modules.chatgpt import chatgpt
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
        # 'question_view.json' からモーダルの定義を読み込む
        with open('json/question_view.json', 'r') as file:
            modal_view = json.load(file)
        modal_view["private_metadata"] = f"{ch_id},{team_domain}"

        client.views_open(
            trigger_id=body["trigger_id"],
            view=modal_view
        )
        # del_message関数の実装内容に基づいて適宜修正
        del_message(ch_id, ts)

    @app.view("modal-submit")
    def modal_submit(ack, body, view, client):
        ack()
        ch_id, team_domain = view["private_metadata"].split(",")
        # フォーム（モーダル）で受け取った質問が入ってる変数
        question = body["view"]["state"]["values"]["question-block"]["input_field"]["value"]
        # 入力されたデータをチャンネルに送信する

        thread = client.chat_postMessage(
            channel=ch_id,
            text=f"受け取った質問: {question}"
        )

        thread_ts=thread["ts"]

        notion=client.chat_postMessage(
            channel=ch_id,
            thread_ts=thread_ts,
            text="生成しています。少々お待ちください..."
        )

        response_text = chatgpt(question)

        del_message(ch_id, notion["ts"])

        with open("json/response_question.json") as f:
            answer_view = json.load(f)["blocks"]

        answer_view[2]["elements"][0]["text"] = response_text

        client.chat_postMessage(
            channel=ch_id,
            thread_ts=thread_ts,
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
                            "text": f"*カテゴリ:*  {category}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*追加日:*  {date}"
                        }
                    ]
                }
            )


        client.chat_postMessage(
            channel=ch_id,
            thread_ts=thread_ts,
            blocks=similar_view
        )

        summary_prompt = question + "\n\nこの内容をタイトル風にして。"
        url = f"https://{team_domain}.slack.com/archives/{ch_id}/p{thread_ts}" # スレッドのURLを作成
        active_start(thread_ts , summary_prompt, url, "稼働中")



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
        del_message(body["channel"]["id"], body["message"]["ts"])

    @app.view("search_modal")
    def handle_search_submission(ack, body, client, view):
        ack()
        search_query = view["state"]["values"]["search_query"]["input"]["value"]
        top_5_similar_texts = get_top_5_similar_texts(search_query)
        # 結果を表示
        response_text = "*検索結果*:\n\n"
        for similarity, content, url, date, category in top_5_similar_texts:
            response_text += f"*Content:* {content}\n"
            response_text += f"*URL:* <{url}|Link>\n"
            response_text += f"*Date:* {date}\n"
            response_text += f"*Category:* {category}\n\n"
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

        ch_id = body["channel"]["id"]
        ts = body["message"]["ts"]

        # del_message関数の実装内容に基づいて適宜修正
        del_message(ch_id, ts)

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

        ch_id = body["channel"]["id"]
        ts = body["message"]["ts"]

        # del_message関数の実装内容に基づいて適宜修正
        del_message(ch_id, ts)

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


    """
    スレッドをDBに保存するためのモーダルの処理

        1. @app.message_shortcut("save)
            ここで一番最初に起動するタイトルの設定方法（手動設定 or 自動生成）を選ぶモーダルを起動。
            channel_id, thread_ts, team_domainを取得し、モーダルビューのprivate_metadataに渡し、データを保持。（"_"が無いとタイトルの再生生成時にエラーになる）
            private_metadataを含んだモーダルビューを表示させ、ユーザーにスレッドのタイトルの設定方法を選ばせる。

        2. @app.action("self")
            ここではユーザーが手動でスレッドタイトルを入力し設定するモーダルを表示する。
            前回のモーダルビューの private_metadata からchannel_id, thread_id, team_domainを取得。
            private_metadataにユーザがタイトルを付けたことを示す、selfを追加した channel_id, thread_ts, self, team_domainを渡し、データを保持。

        3. @app.action("generate")
            ここではスレッドタイトルを自動生成するモーダルを起動する。
            前回のモーダルビューの private_metadata から ch_id, thread_ts, team_domain を取得。
            生成中を伝えるモーダルビューに private_metadata を渡し、モーダルを開く。
            GPT-4に問い合わせてタイトルを生成する。
            生成したタイトルを表示するモーダルビューに生成したタイトルと private_metadata を追加する。
            生成したタイトルを表示するモーダルを表示する。
            (このモーダルには再生成ボタンがあり、ユーザーがそれを押すとこのセクションの処理を繰り返す。)

        4. @app.view("save_submit")
            2か3でsubmit(保存ボタン)が押されるとこのセクションの処理が行われる。
            一番最初にスレッドが保存中の旨を伝えるモーダルが開く。
            前回のモーダルから private_metadata を受け取る。
            受け取った情報に self が含まれてる場合、ユーザー自身がタイトルを設定したタイトルを取得する。
            保存する内容を表示するモーダルビューを作成し、起動する。
            スレッドの保存し、ステータスを停止にする。
            スレッドの要約を生成。
            スレッドの要約のメッセージの block kit を作成し、スレッドに投稿する。
    """
    # タイトルの設定方法を選択
    @app.message_shortcut("save")
    def select_save_modal(ack, body, client):
        ack()
        ch_id = body["channel"]["id"] # ch_id取得
        thread_ts = body["message"]["thread_ts"] # thread_ts取得
        team_domain = body["team"]["domain"] # team_domain取得

        with open("json/save_modal.json") as f:
            modal_view = json.load(f) # jsonからmodal_view読込

        modal_view["select"]["private_metadata"] = f"{ch_id},{thread_ts},_,{team_domain}" # private_metadataを追加

        # モーダルを起動
        client.views_open(
            trigger_id=body["trigger_id"],
            view=modal_view["select"]
        )

    # スレッドタイトル手動設定
    @app.action("self")
    def title_save_modal(ack, body, client, logger):
        ack()
        ch_id, thread_ts, _, team_domain = body["view"]["private_metadata"].split(",") # private_metadata からchannel_id, thread_id, team_domainを取得

        # json読込
        with open("json/save_modal.json") as f:
            modal_view = json.load(f)["self"]

        modal_view["private_metadata"] = f"{ch_id},{thread_ts},self,{team_domain}" # private_metadata追加

        # スレッドタイトルを入力するモーダル起動
        client.views_update(
            view_id=body.get("view").get("id"),
            hash=body.get("view").get("hash"),
            view=modal_view
        )

    # スレッドタイトル自動生成
    @app.action("generate")
    def generate_title_modal(ack, body, client):
        ack()
        ch_id, thread_ts, _, team_domain = body["view"]["private_metadata"].split(",") # private_metadata取得

        # json読込
        with open("json/save_modal.json") as f:
            modal_view = json.load(f)

        modal_view["loading"]["private_metadata"] = f"{ch_id},{thread_ts},_,{team_domain}" # private_metadata追加

        # 「生成中...」モーダル起動
        client.views_update(
            view_id=body.get("view").get("id"),
            hash=body.get("view").get("hash"),
            view=modal_view["loading"]
        )

        title = get_thread_title(client, ch_id, thread_ts) # タイトル生成

        modal_view["generate"]["blocks"][1]["text"]["text"] = f"```{title}```" # 生成したタイトルをビューに設定
        modal_view["generate"]["private_metadata"] = f"{ch_id},{thread_ts},{title},{team_domain}" # private_metadata追加

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

        ch_id, thread_ts, title, team_domain = body["view"]["private_metadata"].split(",") # private_metadata取得

        if title == "self": # タイトルを手動設定した場合
            title = body["view"]["state"]["values"]["title"]["title_input"]["value"] # 入力されたタイトル取得

        # スレッドのURLを作成
        url = f"https://{team_domain}.slack.com/archives/{ch_id}/p{thread_ts}"

        date = datetime.now().date() # 現在日取得

        # 保存した内容を表示するモーダルビュー作成
        modal_view["end"]["blocks"][2]["elements"][0]["text"] = f"<{url}|{title}>"
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
        summary, question, conclusion = summary.split("\n") # 生成した内容を「要約」「質問」「結論」に分ける

        # block_kitを作成
        modal_view["post_summary"]["blocks"][1]["elements"][0]["text"] = question[3:]
        modal_view["post_summary"]["blocks"][4]["elements"][0]["text"] = summary[3:]
        modal_view["post_summary"]["blocks"][7]["elements"][0]["text"] = conclusion[3:]

        # スレッドに要約を投稿
        client.chat_postMessage(
            channel=ch_id,
            thread_ts=thread_ts,
            blocks=modal_view["post_summary"]["blocks"]
        )


    @app.action("thread_monitor")
    def thread_monitor_modal(ack, body, client):
        ack()
        ch_id = body["channel"]["id"]
        ts = body["message"]["ts"]
        active_thread = get_thread_info()

        with open("json/active_thread_list.json") as f:
            modal_view = json.load(f)




        url = active_thread[0]
        response = execute_query("SELECT content, category, date FROM phese4 WHERE url = %s;", url)
        modal_view["block"][0]["text"]["text"] = f"*<{url}|{response[0][0]}>*"
        modal_view["block"][1]["fields"][0]["text"] = f"*カテゴリ:*\n{response[0][1]}"
        modal_view["block"][1]["fields"][1]["text"] = f"*追加日:*\n{response[0][2]}"
        modal_view["modal"]["blocks"].extend(modal_view["block"])

        client.views_update(
            trigger_id=body["trigger_id"],
            view=modal_view["modal"]
        )

        del_message(ch_id, ts)