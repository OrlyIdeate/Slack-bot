def generate_slack_message():
    return {
	"blocks": [
		{
			"type": "header",
			"text": {
				"type": "plain_text",
				"text": "SlackGPTを利用"
			}
		},
		{
			"type": "divider"
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "こんにちは！\n私はSlackGPTです！\nあなたが疑問に思っていることを社内で共有しませんか？\n私が質問を蓄積し、これまでに似た質問があればお答えいたします！"
			}
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
					"action_id": "question"
				},
				{
					"type": "button",
					"text": {
						"type": "plain_text",
						"text": "検索"
					},
					"value": "search",
					"action_id": "search"
				},
				{
					"type": "button",
					"text": {
						"type": "plain_text",
						"text": "一覧表示"
					},
					"value": "list",
					"action_id": "db_list"
				},
				{
					"type": "button",
					"text": {
						"type": "plain_text",
						"text": "アップロード"
					},
					"value": "upload",
					"action_id": "upload"
				}
			]
		}
	]
}

def kit_generate1(con):
    return {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*検索結果*"
                }
            },
            {
			    "type": "divider"
		    },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": con
                }
            }
        ]
    }
def kit_generate2():
    return {
        "blocks" : [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*類似度が高い質問一覧*"
                }
            },
            {
			    "type": "divider"
		    }
        ]
    }
def kit_generate3(rui, now):
    return {
        "blocks" : [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*="+ str(now) +"=*"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": rui
                }
            }
        ]
    }
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
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "アップロード"
                        },
                        "value": "upload",
                        "action_id": "upload"
                    }
                ]
            }
        ]
    }