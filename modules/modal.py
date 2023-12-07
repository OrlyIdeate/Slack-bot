from slack_bolt import App
from slack_sdk import WebClient

def register_modal_handlers(app: App):
    @app.shortcut("modal-shortcut")
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
    def modal_submit(ack, body, client, respond):
        ack()
        # フォーム（モーダル）で受け取った質問が入ってる変数
        question = body["view"]["state"]["values"]["question-block"]["input_field"]["value"]
        # 入力されたデータをチャンネルに送信する
        channel_id = "C067ALJLXRQ"  # メッセージを送信するチャンネルのIDに置き換えてください

        client.chat_postMessage(
            channel=channel_id,
            text=f"受け取った質問: {question}"
        )