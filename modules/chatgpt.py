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
        message_user = event.get('user') # 質問を行った人を取得

        temp = client.chat_postMessage(
            channel=channel_id,
            text="生成しています。しばらくお待ち下さい...:now_loading:",
            thread_ts=thread_ts
        )
        thread_info = client.conversations_replies(channel=channel_id, ts=thread_ts) # ここまでの会話を取得
        #それていないときのメッセージ作成
        question_1 = "以下の会話の最後にユーザーが行った質問は質問として意図が明確ですか？明確なときは「問題ないです」とのみ出力してください。不十分であれば不十分である旨と何が不十分なのかを教えてください。ただし、この質問が出るまでの会話の内容は以下のとおりです。各行に{ユーザー名}:{チャット内容}の形で表しています。回答の際には「U067CHBEU86:」などのユーザーを表記しなくていいです。\n"
        question_2 = "以下の会話の最後にユーザーがしている質問に回答してください。会話は各行に{ユーザー名}:{チャット内容}の形で表しています。回答の際には「U067CHBEU86:」などのユーザーを表記しなくていいです。\n"

        prev_context="" # 過去の会話記録を保存する変数を作成

        cnt=0 # 類似したコンテンツのメッセージ以外を取得し、message_textに追加
        for i in range(len(thread_info['messages'])):
            if cnt != 1:
                prev_context+=thread_info['messages'][i]['user']+": "+thread_info['messages'][i]['text']+"\n"
                # prev_context+=thread_info['messages'][i]['text']+"\n"
            cnt+=1

        #過去の会話記録を生データに追加
        question_1 += prev_context
        question_2 += prev_context

        #質問を生データに追加
        question_1 += message_user + ": " + message_text + "\n"
        question_2 += message_user + ": " + message_text + "\n"

        result_1=chatgpt(question_1) # 質問が明確かどうかの結果

        if "問題ないです" in result_1:
            result_2 = chatgpt(question_2)
            #now_loadingを消す
            client.chat_delete(
                channel=channel_id,
                ts=temp['ts']
            )
            client.chat_postMessage(
                channel=channel_id,
                text=result_2,
                thread_ts=thread_ts
            )
        else:
            #now_loadingを消す
            client.chat_delete(
                channel=channel_id,
                ts=temp['ts']
            )
            client.chat_postMessage(
                channel=channel_id,
                text=result_1,
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



def censor_gpt(question):
    """質問がベストプラクティスに基づいているか検閲します。\n\n

        引数: question (str): 質問\n
        戻り値: str
    """
    openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

    chat_completion = openai_client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": """ユーザーのプロンプトがベストプラクティスに基づいている場合のみ、回答してください。\n
                    プロンプトがベストプラクティスに基づいていない場合は、不十分な点を回答してください。\n
                    ベストプラクティス:```\n
                    指示が明示的である。\n
                    具体的かつ詳細な指示である。\n
                    量などを指示している場合は「なるべく」「かなり」「少なく」「ある程度」などの形容表現ではなく、「3〜5文」「3点」などの数字での指示である。\n
                    ```\n
                    ベストプラクティスに基づいていないときの出力形式:```\n
                    質問がベストプラクティスに基づいていません。\n
                    *不十分な点*\n
                    {不十分だった点を箇条書き}\n
                    *改善例*\n
                    {改善の仕方}\n
                    ```
                    ベストプラクティスに基づいているときは質問への回答のみを返してください。
                    """
            },
            {
                "role": "user", "content": question
            }
        ],
        model="gpt-4",
    )

    return chat_completion.choices[0].message.content


def stream_chat(question):
    openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

    chat_completion = openai_client.chat.completions.create(
        messages=[{"role": "user", "content": question}],
        model="gpt-3.5-turbo",
        stream=True
    )

    for chunk in chat_completion:
        yield chunk.choices[0].delta.content