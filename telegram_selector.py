import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

BASE_URL  = f"https://api.telegram.org/bot{BOT_TOKEN}"
TIMEOUT_SECONDS = 300  # 5 minutes to reply, then auto-select

def _send_message(text, parse_mode="HTML", reply_markup=None):
    if not BOT_TOKEN or not CHAT_ID:
        return {}
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        r = requests.post(f"{BASE_URL}/sendMessage", json=payload, timeout=15)
        r.raise_for_status()
        return r.json().get("result", {})
    except Exception as e:
        print(f"⚠️ Telegram sendMessage failed: {e}")
        if parse_mode == "HTML":
            print("🔄 Retrying Telegram sendMessage without HTML parsing...")
            payload["parse_mode"] = None
            try:
                r = requests.post(f"{BASE_URL}/sendMessage", json=payload, timeout=15)
                r.raise_for_status()
                return r.json().get("result", {})
            except Exception as re:
                print(f"⚠️ Telegram sendMessage retry failed: {re}")
        return {}

def _get_updates(offset=None):
    if not BOT_TOKEN or not CHAT_ID:
        return []
    params = {"timeout": 10, "allowed_updates": ["message", "callback_query"]}
    if offset:
        params["offset"] = offset
    try:
        r = requests.get(f"{BASE_URL}/getUpdates", params=params, timeout=15)
        r.raise_for_status()
        return r.json().get("result", [])
    except Exception as e:
        print(f"⚠️ Telegram getUpdates failed: {e}")
        return []

def _answer_callback(callback_id, text="✅ Got it!"):
    if not BOT_TOKEN or not CHAT_ID:
        return
    try:
        requests.post(f"{BASE_URL}/answerCallbackQuery",
                      json={"callback_query_id": callback_id, "text": text},
                      timeout=10)
    except:
        pass

def _edit_message(message_id, text):
    if not BOT_TOKEN or not CHAT_ID:
        return
    try:
        requests.post(f"{BASE_URL}/editMessageText", json={
            "chat_id": CHAT_ID,
            "message_id": message_id,
            "text": text,
            "parse_mode": "HTML"
        }, timeout=10)
    except:
        pass

def send_topic_selection(articles):
    """
    Sends a numbered list of top facts to Telegram with inline buttons for VJ to choose.
    """
    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram not configured — skipping interactive topic selection.")
        return None

    top_articles = articles[:10]
    lines = ["🗞 <b>Simple Tips by VJ — Daily Facts Choice</b>\nPick a number to make today's Shorts:\n"]
    for i, art in enumerate(top_articles, start=1):
        title = art.get("title", "Untitled")[:80]
        category = art.get("category", "")
        lines.append(f"<b>{i}.</b> {title} ({category})")

    lines.append(f"\n⏳ <i>Auto-selecting #1 in 5 minutes if no response...</i>")
    message_text = "\n".join(lines)

    rows = []
    row  = []
    for i in range(1, len(top_articles) + 1):
        row.append({"text": str(i), "callback_data": str(i)})
        if len(row) == 5:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    keyboard = {"inline_keyboard": rows}

    msg = _send_message(message_text, reply_markup=keyboard)
    sent_message_id = msg.get("message_id")
    print(f"Sent {len(top_articles)} facts to Telegram. Waiting for VJ to select...")

    deadline = time.time() + TIMEOUT_SECONDS
    last_update_id = None

    stale = _get_updates()
    if stale:
        last_update_id = stale[-1]["update_id"] + 1

    while time.time() < deadline:
        try:
            updates = _get_updates(offset=last_update_id)
        except Exception as e:
            print(f"Telegram poll error: {e}")
            time.sleep(5)
            continue

        for update in updates:
            last_update_id = update["update_id"] + 1
            choice = None

            if "callback_query" in update:
                cb = update["callback_query"]
                if str(cb["message"]["chat"]["id"]) == str(CHAT_ID):
                    choice = cb["data"].strip()
                    _answer_callback(cb["id"], f"Selected #{choice} ✅")

            elif "message" in update:
                m = update["message"]
                if str(m["chat"]["id"]) == str(CHAT_ID) and "text" in m:
                    choice = m["text"].strip()

            if choice and choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(top_articles):
                    chosen = top_articles[idx]
                    confirm = (
                        f"✅ <b>Selected #{choice}:</b>\n"
                        f"{chosen.get('title', '')}\n\n"
                        f"🎬 <i>Rendering VJ's fact video now...</i>"
                    )
                    if sent_message_id:
                        _edit_message(sent_message_id, confirm)
                    else:
                        _send_message(confirm)
                    return chosen

        time.sleep(3)

    print("Telegram selection timed out. Auto-selecting #1.")
    if sent_message_id:
        _edit_message(sent_message_id, "⏰ <b>Timed out.</b> Gemini auto-selected #1...")
    return None

def _send_photo(photo_path, caption=""):
    if not BOT_TOKEN or not CHAT_ID:
        return {}
    try:
        with open(photo_path, "rb") as f:
            r = requests.post(
                f"{BASE_URL}/sendPhoto",
                data={"chat_id": CHAT_ID, "caption": caption, "parse_mode": "HTML"},
                files={"photo": f},
                timeout=30
            )
        return r.json().get("result", {})
    except Exception as e:
        print(f"⚠️ Telegram sendPhoto failed: {e}")
        return {}

def send_upload_consent(thumbnail_path, title, duration_sec):
    """
    Sends the compiled video status and thumbnail to Telegram as a notification
    and automatically returns True to auto-approve the upload.
    """
    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram not configured — auto-approving upload.")
        return True

    mins, secs = divmod(int(duration_sec), 60)
    duration_str = f"{mins}m {secs}s" if mins else f"{secs}s"

    caption = (
        f"🎬 <b>VJ Videos - Video Compiled!</b>\n\n"
        f"📌 <b>Title:</b> {title}\n"
        f"⏱ <b>Duration:</b> {duration_str}\n\n"
        f"🚀 <i>Auto-uploading to VJ Videos YouTube Channel now...</i>"
    )

    try:
        if thumbnail_path and os.path.exists(thumbnail_path):
            _send_photo(thumbnail_path, caption)
        else:
            _send_message(caption)
    except Exception as e:
        print(f"Telegram photo send failed: {e}")
        _send_message(caption)

    return True

def notify_telegram(message, emoji="ℹ️"):
    if BOT_TOKEN and CHAT_ID:
        try:
            _send_message(f"{emoji} {message}")
        except Exception as e:
            print(f"Telegram notify failed: {e}")
