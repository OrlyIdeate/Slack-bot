# e3sysカタパルト2023 （SlackApp）

これは、データエンジニアカタパルト2023年のPhase4のチームe3sysのプロジェクトです。

<br>

## インストール

Ubuntu-20.04環境でのコマンドを記載してます

1. リポジトリをクローン
    ```
    git clone https://github.com/OrlyIdeate/Slack-bot.git
    ```

2. ディレクトリに移動
    ```
    cd Slack-bot
    ```

3. 仮想環境構築
    ```
    python -m venv .venv
    ```

4. 仮想環境実行
    ```
    source .venv/bin/activate
    ```

5. ライブラリをインストール
    ```
    pip install -r requirements.txt
    ```

6. `.env.sample`ファイルを元に`.env`ファイルを作成
    ```
    # 自作モジュールのファイルパス
    PYTHONPATH=$/home/{ユーザー名}/Slack-bot/modules

    /// 省略

    # Slack関係のキー
    SLACK_BOT_TOKEN="xoxb-{Slackのボットトークン}"
    SLACK_APP_TOKEN="xapp-{Slackのアプリトークン}"

    # OpenAI関係のキー
    OPENAI_API_KEY="sk-{OpenAIのAPIキー}"
    ```
<br>

## 使用方法

1. 仮想環境の起動
    ```
    source .venv/bin/activate
    ```


2. Slackアプリ(Bot)を起動
    ```
    python app.py
    ```

3. Slackアプリ(Bot)を停止
    ```
    ctrl + c
    ```

4. 仮想環境の停止
    ```
    deactivate
    ```

<br>

## `requirements.txt`への追記のやり方
ターミナルで以下のコマンドを実行してください。
```
pip freeze > requirements.txt
```