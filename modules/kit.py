def generate_slack_message():
    return {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "こんにちは！私はSlackGPTです！あなたが疑問に思っていることを社内で共有しませんか？私が質問を蓄積し、これまでに似た質問があればお答えいたします！"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "input",
                "element": {
                    "type": "plain_text_input",
                    "multiline": True,
                    "action_id": "plain_text_input-action"
                },
                "label": {
                    "type": "plain_text",
                    "text": "質問入力欄"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "送信"
                        },
                        "action_id": "send_button-action"
                    }
                ]
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "質問"
                        },
                        "value": "question",
                        "action_id": "modal-shortcut"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "検索"
                        },
                        "value": "search",
                        "action_id": "open_search_modal"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "一覧表示"
                        },
                        "value": "list",
                        "action_id": "db_list"
                    }
                ]
            }
        ]
    }