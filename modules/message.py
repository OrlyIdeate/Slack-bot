import os
import openai
from slack_bolt import App
from slack_sdk.web import WebClient
import mysql.connector

# .env読み込み
from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")


def message(app: App):
    @app.event("message")
    def distraction_checker(message, say):
        print("distraction_checkerが動いています")
        openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
        slack_client = WebClient(token=SLACK_BOT_TOKEN)
        message_channel = message['channel']
        message_ts = message['ts']
        message_thread_ts = message.get('thread_ts')
        if message_thread_ts is None:
            return
        thread_ts = message_thread_ts
        #スレッドでのチャットが何個目かを取得してthread_countにいれる
        config = {
            'user': 'root',
            'password': 'citson-buzrit-4cyxZu',
            'host': '35.223.243.48',
            'database': 'test1',
        }
        db_connection = mysql.connector.connect(**config)
        cursor = db_connection.cursor()
        thread_count_query = f"SELECT message_count FROM thread_monitoring WHERE thread_id = '{thread_ts}'"
        cursor.execute(thread_count_query)
        thread_count_result = cursor.fetchone()
        if thread_count_result is not None:
            thread_count = thread_count_result[0]
        else:
            insert_query = f"INSERT INTO thread_monitoring (thread_id, message_count) VALUES ('{thread_ts}', 1)"
            cursor.execute(insert_query)
            thread_count = 1
        update_query = f"UPDATE thread_monitoring SET message_count = message_count + 1 WHERE thread_id = '{thread_ts}'"
        cursor.execute(update_query)
        db_connection.commit()
        cursor.close()
        db_connection.close()
        response = slack_client.chat_postMessage(
            channel=message_channel,
            text=str(thread_count),
            thread_ts=message_thread_ts
        )
        if thread_count % 10 == 0:
            #これまでの会話ログとスレッドの最初の質問を取得
            prev_message = slack_client.conversations_replies(channel=message_channel, ts=message_thread_ts)
            ques = prev_message['messages'][0]['text']
            all_message= ""
            for i in range(len(prev_message['messages'])):
                all_message+=prev_message['messages'][i]['text']
            message_text_with_instruction = all_message + "\nここまでの文言は以下の質問に対する直近の会議内容です。\n" + ques + "\n質問から会議がそれてきていると考えるならば「それています」とのみ出力し、それていない場合は「それていません」とのみ出力してください。"
            chat_completion = openai_client.chat.completions.create(
                messages=[{"role": "user", "content": message_text_with_instruction}],
                model="gpt-4"
            )
            response_text = chat_completion.choices[0].message.content
            if "それています" in response_text:
                # スレッド内に返信を送信
                response = slack_client.chat_postMessage(
                    channel=message_channel,
                    text="話の内容が質問内容からそれていませんか? 今日の晩御飯の話なら別のチャンネルでお願いします。",
                    thread_ts=message_thread_ts
                )
            else:
                response = slack_client.chat_postMessage(
                    channel=message_channel,
                    text=thread_count,
                    thread_ts=message_thread_ts
                )
        return
