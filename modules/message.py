"""
スレッド内でのディスカッションが最初の話題からそれていないかをチェックします。
スレッドに10回メッセージが送信されるとスレッド内のテキストをすべて取得し Chat-GPT に会話がそれていないかチェックしてもらいます。
"""
from modules.DB import execute_query
from modules.chatgpt import chatgpt

def message(app):
    @app.event("message")
    def distraction_checker(message, client):
        print("distraction_checkerが動いています")


        message_channel = message['channel']
        message_ts = message['ts']
        thread_ts = message.get('thread_ts')


        #スレッドでのチャットが何個目かを取得してthread_countにいれる
        thread_count_query = f"SELECT message_count FROM thread_monitoring WHERE thread_id = '{thread_ts}'"
        thread_count_result = execute_query(thread_count_query)

        if thread_count_result and len(thread_count_result) > 0:
            # リストが空でない場合、最初の要素を取得
            thread_count = thread_count_result[0][0]  # 最初の要素の最初のカラム
        else:
            # リストが空の場合、新しいスレッドカウントを挿入
            insert_query = f"INSERT INTO thread_monitoring (thread_id, message_count) VALUES ('{thread_ts}', 1)"
            execute_query(insert_query)
            thread_count = 1

        update_query = f"UPDATE thread_monitoring SET message_count = message_count + 1 WHERE thread_id = '{thread_ts}'"
        execute_query(update_query)

        if thread_count % 15 == 0:
            #これまでの会話ログとスレッドの最初の質問を取得
            prev_message = client.conversations_replies(channel=message_channel, ts=thread_ts)
            ques = prev_message['messages'][0]['text']
            all_message= ""
            for i in range(len(prev_message['messages'])):
                all_message+=prev_message['messages'][i]['text']
            message_text_with_instruction = all_message + "\nここまでの文言は以下の質問に対する直近の会議内容です。\n" + ques + "\n質問から会議がものすごくそれてきていると考えるならば「それています」とのみ出力し、それていない場合は「それていません」とのみ出力してください。"

            response_text = chatgpt(message_text_with_instruction)
            if "それています" in response_text:
                # スレッド内に返信を送信
                client.chat_postMessage(
                    channel=message_channel,
                    text="話の内容が質問内容からそれていませんか?",
                    thread_ts=thread_ts
                )