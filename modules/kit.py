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
			    			"text": "Button 1"
			    		},
			    		"value": "button_1",
			    		"action_id": "actionId-1"
			    	},
			    	{
			    		"type": "button",
			    		"text": {
			    			"type": "plain_text",
			       			"text": "Button 2"
			    		},
			    		"value": "button_2",
		    			"action_id": "actionId-2"
		    		},
		    		{
		    			"type": "button",
		    			"text": {
		    				"type": "plain_text",
					        "text": "Button 3"
				        },
				        "value": "button_3",
				        "action_id": "actionId-3"
			        }
			    ]
		    }
	    ]
    }