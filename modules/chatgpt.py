import os
from slack_bolt import App
from slack_sdk.web import WebClient
import openai

# .env読み込み
from dotenv import load_dotenv
load_dotenv()

from modules.similarity import get_top_5_similar_texts
from modules.kit import kit_generate1
from modules.kit import kit_generate2
from modules.kit import kit_generate3

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

def generator_answer_gpt(app: App):
    @app.message("@GPT")
    def ret_gpt(message, say):
        openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
        slack_client = WebClient(token=SLACK_BOT_TOKEN)
        message_channel = message['channel']
        message_thread_ts = message['ts']
        message_true_thread_ts = message.get('thread_ts')
        print(message_channel)
        print("GPTの1が動いています")
        message_text = message['text']
        message_text += "\nという質問は質問として十分ですか？不十分ですか？十分のときはそれが十分であることを言う必要はなく、質問の回答だけを表示してください。不十分であれば回答はせずに不十分である旨と何が不十分なのかを教えてください。ただし、この質問が出るまでの会話の内容は以下のとおりです。各行に{ユーザー名}:{チャット内容}の形で表しています。\n"
        prev_message = slack_client.conversations_replies(channel=message_channel, ts=message_true_thread_ts)
        for i in range(len(prev_message['messages'])):
            message_text+=prev_message['messages'][i]['user']+": "+prev_message['messages'][i]['text']+"\n"
        chat_completion = openai_client.chat.completions.create(
            messages=[{"role": "user", "content": message_text}],
            model="gpt-4"
        )
        response_text = chat_completion.choices[0].message.content

        response = slack_client.chat_postMessage(
            channel=message_channel,
            text=response_text,
            thread_ts=message_thread_ts
        )
        return


def chatgpt(message):
        openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
        message_text = message

        chat_completion = openai_client.chat.completions.create(
            messages=[{"role": "user", "content": message_text}],
            model="gpt-4"
        )

        response_text = chat_completion.choices[0].message.content
        top_5_similar_texts = get_top_5_similar_texts(message_text)
        response = []
        response.append(kit_generate1(response_text))
        now=1
        for similarity, content, url, date in top_5_similar_texts:
            response.append(kit_generate3("*内容* : " + content + "\n*日付* : " + str(date) + "\n*url* : <"+ url +"|こちらから飛べます>", now))
            now+=1
        return response