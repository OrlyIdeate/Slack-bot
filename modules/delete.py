import os
from dotenv import load_dotenv
from slack_sdk import WebClient

load_dotenv()
client = WebClient(os.getenv("SLACK_BOT_TOKEN"))

def del_message(channel_id, ts):
    """メッセージを削除します。

    引数:
        channel_id: チャンネルID
        ts: 削除したいメッセージのタイムスタンプ
    """
    client.chat_delete(
                channel=channel_id,
                ts=ts
            )