import os
import openai
from slack_bolt import App

# .env読み込み
from dotenv import load_dotenv
load_dotenv()


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def generator_answer_gpt(app: App):
    """メンションでの質問に回答する。

    引数:
        app (App)
    """
    @app.event({"type": "app_mention"})
    def generate_answer(event, client):
        channel_id = event.get("channel") # チャンネルID取得
        thread_ts = event.get('thread_ts') # スレッドのタイムスタンプを取得
        message_text = event.get('text') # 質問の内容を取得

        # スレッド内の会話を取得
        # message_text += "\nという質問は質問として十分ですか？不十分ですか？十分のときはそれが十分であることを言う必要はなく、質問の回答だけを表示してください。不十分であれば回答はせずに不十分である旨と何が不十分なのかを教えてください。ただし、この質問が出るまでの会話の内容は以下のとおりです。各行に{ユーザー名}:{チャット内容}の形で表しています。\n"
        message_text += "\n 過去の会話を踏まえて答えてください。各行に{ユーザー名}:{チャット内容}の形で表しています。\n"
        thread_info = client.conversations_replies(channel=channel_id, ts=thread_ts)

        cnt=0 # 類似したコンテンツのメッセージ以外を取得し、message_textに追加
        for i in range(len(thread_info['messages'])):
            if cnt != 1:
                # message_text+=thread_info['messages'][i]['user']+": "+thread_info['messages'][i]['text']+"\n"
                message_text+=thread_info['messages'][i]['text']+"\n"
            cnt+=1

        client.chat_postMessage(
            channel=channel_id,
            text=chatgpt(message_text),
            thread_ts=thread_ts
        )


def chatgpt(message):
    """引数に渡した内容をChat-GPT4に入力し、回答を返す。

    引数:
        event (str): Chat-GPT4に入力するプロンプト

    返り値:
        str: Chat-GPT4が生成した回答
    """
    openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

    chat_completion = openai_client.chat.completions.create(
        messages=[{"role": "user", "content": message}],
        model="gpt-4"
    )

    response = chat_completion.choices[0].message.content

    return response