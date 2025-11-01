#!/usr/bin/env python3
import os, json, time, requests, random
from pathlib import Path

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
SIGNALS_SOURCE = os.environ.get("SIGNALS_SOURCE", "signals.json")
POSTED_FILE = Path("posted.json")

MIN_DELAY_SEC = float(os.environ.get("MIN_DELAY_SEC", "4.0"))
MAX_DELAY_SEC = float(os.environ.get("MAX_DELAY_SEC", "7.0"))
LOOP_SLEEP_SEC = float(os.environ.get("LOOP_SLEEP_SEC", "30.0"))

def load_signals():
    if SIGNALS_SOURCE.startswith("http"):
        r = requests.get(SIGNALS_SOURCE, timeout=10)
        r.raise_for_status()
        return r.json()
    with open(SIGNALS_SOURCE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_posted(): return set(json.loads(POSTED_FILE.read_text(encoding="utf-8"))) if POSTED_FILE.exists() else set()
def save_posted(data): POSTED_FILE.write_text(json.dumps(list(data)), encoding="utf-8")

def send_message_safe(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": text, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 429:
            retry = r.json().get("parameters", {}).get("retry_after", 10)
            print("429 recebido, esperando", retry, "s")
            time.sleep(retry + 2)
            return False
        r.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print("Erro ao enviar:", e)
        return False

def format_signal(s):
    return f"🎰 <b>{s.get('slot')}</b>\n🕐 {s.get('time')}\n💬 {s.get('note','')}"

def main_loop():
    if not BOT_TOKEN or not CHANNEL_ID:
        raise SystemExit("BOT_TOKEN ou CHANNEL_ID faltando")
    posted = load_posted()
    while True:
        try:
            signals = load_signals()
            for s in signals:
                sid = str(s.get("id") or (s.get("slot","") + s.get("time","")))
                if sid in posted: continue
                text = format_signal(s)
                if send_message_safe(text):
                    posted.add(sid)
                    save_posted(posted)
                    delay = MIN_DELAY_SEC + random.random() * (MAX_DELAY_SEC - MIN_DELAY_SEC)
                    print(f"Enviado {sid} - aguardando {delay:.1f}s")
                    time.sleep(delay)
            time.sleep(LOOP_SLEEP_SEC)
        except Exception as e:
            print("Erro no loop:", e)
            time.sleep(10)

if __name__ == "__main__":
    main_loop()
