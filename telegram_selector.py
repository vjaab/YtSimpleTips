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
            payload.pop("parse_mode", None)
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
    data = {"chat_id": CHAT_ID, "caption": caption, "parse_mode": "HTML"}
    try:
        with open(photo_path, "rb") as f:
            r = requests.post(
                f"{BASE_URL}/sendPhoto",
                data=data,
                files={"photo": f},
                timeout=30
            )
            r.raise_for_status()
        return r.json().get("result", {})
    except Exception as e:
        print(f"⚠️ Telegram sendPhoto failed: {e}")
        print("🔄 Retrying Telegram sendPhoto without HTML parsing...")
        data.pop("parse_mode", None)
        try:
            with open(photo_path, "rb") as f:
                r = requests.post(
                    f"{BASE_URL}/sendPhoto",
                    data=data,
                    files={"photo": f},
                    timeout=30
                )
                r.raise_for_status()
            return r.json().get("result", {})
        except Exception as re:
            print(f"⚠️ Telegram sendPhoto retry failed: {re}")
        return {}

import json

def _send_media_group(photo_paths, caption=""):
    if not BOT_TOKEN or not CHAT_ID:
        return []
    media = []
    for i, path in enumerate(photo_paths):
        media.append({
            "type": "photo",
            "media": f"attach://photo{i}",
        })
    if media and caption:
        media[0]["caption"] = caption
        media[0]["parse_mode"] = "HTML"
        
    files = {}
    for i, path in enumerate(photo_paths):
        files[f"photo{i}"] = open(path, "rb")
        
    try:
        r = requests.post(f"{BASE_URL}/sendMediaGroup", data={"chat_id": CHAT_ID, "media": json.dumps(media)}, files=files, timeout=30)
        r.raise_for_status()
        return r.json().get("result", [])
    except Exception as e:
        print(f"⚠️ Telegram sendMediaGroup failed: {e}")
        return []
    finally:
        for f in files.values():
            f.close()

def send_upload_consent(thumbnail_paths, title_variants, duration_sec):
    """
    Sends all thumbnail variants and title options to Telegram.
    Presents an interactive inline keyboard allowing VJ to toggle selections
    and approve the final upload.
    """
    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram not configured — auto-approving default upload choice.")
        return {
            "title": title_variants[0] if title_variants else "Default Title",
            "thumbnail": thumbnail_paths[0] if thumbnail_paths else ""
        }
        
    try:
        # Send the media group first so VJ can see all 3 thumbnails
        _send_media_group(thumbnail_paths, caption="📷 Here are the generated thumbnails (A, B, C)")
    except Exception as e:
        print(f"⚠️ Failed to send media group: {e}")
    
    # Store currently selected indices (0-indexed)
    state = {
        "title_idx": 0,
        "thumb_idx": 0
    }
    
    def get_keyboard_markup():
        # Title Selection buttons
        title_buttons = []
        for idx in range(3):
            label = f"Title {idx+1}"
            if idx == state["title_idx"]:
                label += " 🔘"
            title_buttons.append({"text": label, "callback_data": f"sel_title_{idx}"})
            
        # Thumbnail Selection buttons
        thumb_buttons = []
        for idx, letter in enumerate(["A", "B", "C"]):
            label = f"Thumb {letter}"
            if idx == state["thumb_idx"]:
                label += " 🔘"
            thumb_buttons.append({"text": label, "callback_data": f"sel_thumb_{idx}"})
            
        # Action buttons
        action_buttons = [
            {"text": "✅ Approve & Upload", "callback_data": "approve_upload"}
        ]
        
        return {
            "inline_keyboard": [
                title_buttons,
                thumb_buttons,
                action_buttons
            ]
        }
        
    def get_status_text():
        mins, secs = divmod(int(duration_sec), 60)
        dur_str = f"{mins}m {secs}s" if mins else f"{secs}s"
        
        t_letter = ["A", "B", "C"][state["thumb_idx"]]
        
        return (
            f"🎬 <b>VJ Videos - Video Ready for Approval</b>\n\n"
            f"⏱ <b>Duration:</b> {dur_str}\n\n"
            f"📝 <b>Titles:</b>\n"
            f"1. {title_variants[0]}\n"
            f"2. {title_variants[1]}\n"
            f"3. {title_variants[2]}\n\n"
            f"👉 <b>Current Selection:</b>\n"
            f"• Title: Variant {state['title_idx'] + 1}\n"
            f"• Thumbnail: Variant {t_letter}\n\n"
            f"⏳ <i>Auto-approving Title 1 & Thumbnail A in 5 minutes on timeout...</i>"
        )

    # Send control message
    msg = _send_message(get_status_text(), reply_markup=get_keyboard_markup())
    sent_message_id = msg.get("message_id")
    
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
            action = None
            
            if "callback_query" in update:
                cb = update["callback_query"]
                if str(cb["message"]["chat"]["id"]) == str(CHAT_ID):
                    action = cb["data"].strip()
                    
                    if action.startswith("sel_title_"):
                        state["title_idx"] = int(action.split("_")[-1])
                        _answer_callback(cb["id"], f"Selected Title {state['title_idx']+1} 📝")
                        if sent_message_id:
                            requests.post(f"{BASE_URL}/editMessageText", json={
                                "chat_id": CHAT_ID,
                                "message_id": sent_message_id,
                                "text": get_status_text(),
                                "parse_mode": "HTML",
                                "reply_markup": get_keyboard_markup()
                            }, timeout=10)
                            
                    elif action.startswith("sel_thumb_"):
                        state["thumb_idx"] = int(action.split("_")[-1])
                        t_letter = ["A", "B", "C"][state["thumb_idx"]]
                        _answer_callback(cb["id"], f"Selected Thumbnail {t_letter} 📷")
                        if sent_message_id:
                            requests.post(f"{BASE_URL}/editMessageText", json={
                                "chat_id": CHAT_ID,
                                "message_id": sent_message_id,
                                "text": get_status_text(),
                                "parse_mode": "HTML",
                                "reply_markup": get_keyboard_markup()
                            }, timeout=10)
                            
                    elif action == "approve_upload":
                        _answer_callback(cb["id"], "Approved! Uploading... 🚀")
                        confirm_text = (
                            f"✅ <b>VJ Approved Upload!</b>\n\n"
                            f"📌 <b>Final Title:</b> {title_variants[state['title_idx']]}\n"
                            f"🖼️ <b>Thumbnail:</b> Variant {['A', 'B', 'C'][state['thumb_idx']]}\n\n"
                            f"🚀 <i>Uploading now...</i>"
                        )
                        if sent_message_id:
                            _edit_message(sent_message_id, confirm_text)
                        else:
                            _send_message(confirm_text)
                            
                        return {
                            "title": title_variants[state["title_idx"]],
                            "thumbnail": thumbnail_paths[state["thumb_idx"]]
                        }
                        
            elif "message" in update:
                m = update["message"]
                if str(m["chat"]["id"]) == str(CHAT_ID) and "text" in m:
                    text = m["text"].strip().lower()
                    if "approve" in text or "upload" in text or "ok" in text:
                        return {
                            "title": title_variants[state["title_idx"]],
                            "thumbnail": thumbnail_paths[state["thumb_idx"]]
                        }
                        
        time.sleep(3)
        
    print("Telegram selection timed out. Auto-approving default selection.")
    if sent_message_id:
        _edit_message(sent_message_id, "⏰ <b>Timed out.</b> Auto-uploading with default settings (Title 1 & Thumbnail A)...")
        
    return {
        "title": title_variants[0],
        "thumbnail": thumbnail_paths[0]
    }

def notify_telegram(message, emoji="ℹ️"):
    if BOT_TOKEN and CHAT_ID:
        try:
            _send_message(f"{emoji} {message}")
        except Exception as e:
            print(f"Telegram notify failed: {e}")
