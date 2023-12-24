import os
from slack_bolt import App
from slack_bolt.workflows.step import WorkflowStep
from slack_bolt.adapter.socket_mode import SocketModeHandler

# .env読み込み
from dotenv import load_dotenv
load_dotenv()

from modules.kit import generate_slack_message


def workflow_step(app):
    # WorkflowStep 定義

    def edit(ack, step, configure, logger):
        ack()

        blocks = [
            {
                "type": "input",
                "block_id": "select_ch",
                "element": {
                    "type": "channels_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "チャンネルを選んでください"
                    },
                    "action_id": "select_ch"
                },
                "label": {
                    "type": "plain_text",
                    "text": "ワークフローを使用するチャンネル"
                }
            }
        ]
        configure(blocks=blocks)




    def save(ack, body, view, update, logger):
        ack()

        values = view["state"]["values"]
        channel_id = values["select_ch"]["select_ch"]["selected_channel"]

        inputs = {
            "channel": {"value": channel_id}
        }
        update(inputs=inputs)





    def execute(ack, client, step, complete):
        ack()
        ch_id = step["inputs"]["channel"]["value"]

        messages = generate_slack_message()["blocks"]

        response = client.chat_postMessage(
            channel=ch_id,
            blocks=messages
        )


        complete(outputs={})

    # WorkflowStep の新しいインスタンスを作成する
    ws = WorkflowStep(
        callback_id="add_task",
        edit=edit,
        save=save,
        execute=execute,
    )
    # ワークフローステップを渡してリスナーを設定する
    app.step(ws)
