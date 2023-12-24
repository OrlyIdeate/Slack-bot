def del_message(client, body):
    """メッセージを削除します。

    引数:
        client
        body
    """
    client.chat_delete(
                channel=body["container"]["channel_id"],
                ts=body["container"]["message_ts"]
            )