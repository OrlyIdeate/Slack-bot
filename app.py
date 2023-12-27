import os

# Slackライブラリ
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# .env読み込み
from dotenv import load_dotenv
load_dotenv()

# modulesフォルダのユーザー定義関数をインポート
from modules.modal import register_modal_handlers
from modules.chatgpt import generator_answer_gpt
from modules.search import look_for
from modules.show import select_all_db
from modules.message import message
from modules.workflow import workflow_step
from modules.upload import source
from modules.active import thread_monitor

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")

app = App(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)
thread_monitor(app) # 質問に対する結論が出たかどうかを調べる
source(app) # @uploadでデータをDBに保存
look_for(app) # @searchで検索
select_all_db(app) # @showで全データ取得
register_modal_handlers(app) # モーダル起動
generator_answer_gpt(app) # メンションでChatGPTに質問
message(app) # スレッド内の話題がそれていないかを検閲
workflow_step(app) # ワークフローからモーダルを開くためのメッセージを送信

# アプリを起動します
if __name__ == "__main__":
    SocketModeHandler(app, SLACK_APP_TOKEN).start()
