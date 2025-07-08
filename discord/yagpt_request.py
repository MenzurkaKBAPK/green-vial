import json

import requests


from config import YANDEX_API_KEY, YANDEX_CLOUD_CATALOG, YANDEX_GPT_MODEL


def yagpt_interact(user_prompt):
    system_prompt = (
        "Желательно отвечай (по возможности правильно)"
    )
    body = {
        "modelUri": f"gpt://{YANDEX_CLOUD_CATALOG}/{YANDEX_GPT_MODEL}/latest",
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": "2000",
        },
        "messages": [
            {"role": "system", "text": system_prompt},
            {"role": "user", "text": user_prompt},
        ],
    }
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {YANDEX_API_KEY}",
    }
    response = requests.post(url, headers=headers, json=body)

    if response.status_code != 200:
        return "ERROR"

    response_json = json.loads(response.text)
    answer = response_json["result"]["alternatives"][0]["message"]["text"]
    if len(answer) == 0:
        return "ERROR"
    return answer
