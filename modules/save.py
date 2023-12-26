import logging
logging.basicConfig(level=logging.ERROR)

import os
import openai
from slack_bolt import App
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from datetime import datetime
import mysql.connector
import pickle

from dotenv import load_dotenv
load_dotenv()

from modules.similarity import get_embedding
from modules.active import active_end

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

def store_thread(app: App):
    @app.message("@save")
    def get_thread_url(event, say):
        openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
        slack_client = WebClient(token=SLACK_BOT_TOKEN)
        message_channel = event['channel']
        message_thread_ts = event.get('thread_ts', event['ts'])

        # スレッド内の全会話を取得
        prev_message = slack_client.conversations_replies(channel=message_channel, ts=message_thread_ts)
        all_messages = " ".join(msg['text'] for msg in prev_message['messages'])

        # 要約を求めるプロンプト作成
        summary_prompt = all_messages + "\n\nこの会話の要約し、課題と結論をできるだけ短くまとめてください。"

        # GPTへ要約を問い合わせ
        summary_completion = openai_client.chat.completions.create(
            messages=[{"role": "user", "content": summary_prompt}],
            model="gpt-4"
        )
        summary_text = summary_completion.choices[0].message.content

        # 要約をSlackに投稿
        response = slack_client.chat_postMessage(
            channel=message_channel,
            text="会話の要約: " + summary_text,
            thread_ts=message_thread_ts
        )

        first_message_response = slack_client.conversations_replies(channel=message_channel, ts=message_thread_ts)
        first_message_text = first_message_response['messages'][0]['text']

        # 要約を求めるプロンプト作成
        summary_prompt = first_message_text + "\n\nこの内容をタイトル風にして。"

        # GPTへ要約を問い合わせ
        summary_completion = openai_client.chat.completions.create(
            messages=[{"role": "user", "content": summary_prompt}],
            model="gpt-4"
        )
        summary_text = summary_completion.choices[0].message.content

        # スレッドのURLを生成
        # スレッドのURLを生成
        thread_url = f"https://dec-ph4-hq.slack.com/archives/{message_channel}/p{message_thread_ts.replace('.', '')}?thread_ts={message_thread_ts.replace('.', '')}&cid={message_channel}"


        config = {
        'user': 'root',
        'password': 'citson-buzrit-4cyxZu',
        'host': '35.223.243.48',
        'database': 'test1',
        }
        db_connection = mysql.connector.connect(**config)
        cursor = db_connection.cursor()
        text1 = summary_text # 取得してきた質問
        vector1 = get_embedding(text1)
        vector_bytes = pickle.dumps(vector1)

        url = thread_url
        category = "スレッド"

        today = datetime.now()

        # データベースにデータを挿入
        insert_query = "INSERT INTO phese4 (content, vector, url, date, category) VALUES (%s, %s, %s, %s, %s);"
        cursor.execute(insert_query, (text1, vector_bytes, url ,today, category))
        db_connection.commit()

        response = slack_client.chat_postMessage(
            channel=message_channel,
            text="保存された内容:\n " + summary_text,
            thread_ts=message_thread_ts  # スレッドのタイムスタンプを指定
        )

        active_end(message_thread_ts)