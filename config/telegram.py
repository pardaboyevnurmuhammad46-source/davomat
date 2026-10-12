import json
import urllib.error
import urllib.request

from django.conf import settings


def send_telegram(chat_id, text):
    if not settings.BOT_TOKEN or not chat_id:
        return False
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage",
        data=json.dumps({"chat_id": chat_id, "text": text}).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(request, timeout=10)
    except urllib.error.HTTPError as e:
        if e.code in (400, 403):
            return False
        raise
    return True