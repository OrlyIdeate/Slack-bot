import json
from slack_bolt.workflows.step import WorkflowStep
from dotenv import load_dotenv

load_dotenv()

def workflow_step(app):
    # WorkflowStepの定義
    def edit(ack, configure):
        ack()
        with open("json/workflow_step_edit.json") as f:
            configure(blocks=json.load(f)["blocks"])

    def save(ack, view, update):
        ack()
        update(
            inputs={
            "channel": {
                "value": view["state"]["values"]["select_ch"]["select_ch"]["selected_channel"]
                }
            }
        )

    def execute(ack, client, step, complete):
        ack()
        with open("json/first_message.json") as f:
            response = client.chat_postMessage(
                channel=step["inputs"]["channel"]["value"],
                blocks=json.load(f)["blocks"]
            )
        complete(outputs={})

    # 新しいWorkflowStepインスタンスの作成とリスナーの設定
    ws = WorkflowStep(
        callback_id="workflow-step",
        edit=edit,
        save=save,
        execute=execute,
    )
    app.step(ws)