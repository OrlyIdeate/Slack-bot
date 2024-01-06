# 環境変数読込
from dotenv import load_dotenv
load_dotenv()
from modules.chatgpt import chatgpt # Chat-GPTの回答を生成

def get_thread_title(client, channel_id, thread_ts):
    """
    この関数は、指定されたスレッドのタイトルを生成します。
    スレッドの最初のメッセージを基にタイトルを作成します。

    引数:
    client -- Slackのクライアント
    channel_id -- スレッドが存在するチャンネルのID
    thread_ts -- タイトルを生成するスレッドのタイムスタンプ

    戻り値:
    thread_title -- スレッドのタイトル
    """
    prev_message = client.conversations_replies(channel=channel_id, ts=thread_ts) # スレッドの情報を取得
    all_messages = " ".join(msg["text"] for msg in prev_message["messages"]) # スレッド内の全会話を取得

    summary_prompt = all_messages + "\nこの会話に50文字以内でタイトルをつけて" # 最初のメッセージを基に要約を求めるプロンプト作成
    thread_title = chatgpt(summary_prompt) # スレッドのタイトルを生成

    return thread_title # スレッドのタイトル

def get_thread_summary(client, channel_id, thread_ts):
    """
    この関数は、指定されたスレッドの要約を生成します。
    スレッドの全会話を取得し、それを基に要約を作成します。

    引数:
    client -- Slackのクライアント
    channel_id -- スレッドが存在するチャンネルのID
    thread_ts -- 要約するスレッドのタイムスタンプ

    戻り値:
    summary_text -- 要約、質問、結論をカンマ区切りでまとめた文字列
    """
    prev_message = client.conversations_replies(channel=channel_id, ts=thread_ts) # スレッドの情報を取得
    all_messages = " ".join(msg["text"] for msg in prev_message["messages"]) # スレッド内の全会話を取得

    summary_prompt = "以下の会話の内容をまとめた「要約」、一番最初の質問をまとめた「質問」、最終的な結論「結論」をそれぞれ100字以内で出力してください。\n" + f"会話：\n{all_messages}\n" + '{"question": "{質問}", "summary": "{要約}", "conclusion": "{回答}"}\n上記の形式のjsonのみ出力してください。'
    summary_text = chatgpt(summary_prompt)
    # print("スレッド要約依頼の結果:", summary_text)
    return summary_text