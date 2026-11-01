import sys
import os
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

URL = "https://www.sivas.edu.tr/yemek-listesi"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}

AYLAR = {
    "01": "Ocak", "02": "Şubat", "03": "Mart", "04": "Nisan",
    "05": "Mayıs", "06": "Haziran", "07": "Temmuz", "08": "Ağustos",
    "09": "Eylül", "10": "Ekim", "11": "Kasım", "12": "Aralık"
}

def get_menu_by_date(target_date):
    gun = target_date.strftime("%d")
    ay_no = target_date.strftime("%m")
    yil = target_date.strftime("%Y")
    ay_adi = AYLAR.get(ay_no, "")
    aranan_tarih = f"{gun} {ay_adi} {yil}"

    try:
        res = requests.get(URL, headers=HEADERS, timeout=15)
        res.encoding = "utf-8"
        if res.status_code != 200:
            return None

        soup = BeautifulSoup(res.text, "html.parser")
        text = soup.get_text("\n")
        raw_lines = [line.strip() for line in text.splitlines() if line.strip()]

        menu_items = []
        found_date = False

        for i, line in enumerate(raw_lines):
            if aranan_tarih in line:
                found_date = True
                continue

            if found_date:
                if any(day in line for day in ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Hafta"]):
                    break
                
                if "kal" in line:
                    kalori = line
                    if i + 1 < len(raw_lines):
                        sonraki = raw_lines[i + 1]
                        if not any(day in sonraki for day in ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"]):
                            menu_items.append(f"{sonraki} ({kalori})")
                        else:
                            menu_items.append(kalori)
                    else:
                        menu_items.append(kalori)
                elif any(char.isupper() for char in line) and len(line) > 3 and not any(x in line for x in ["12:00", "Öğlen"]):
                    if not any(line in item for item in menu_items):
                        menu_items.append(line)

        if not menu_items:
            return None

        unique_items = list(dict.fromkeys(menu_items))
        return unique_items

    except Exception as e:
        print(f"Hata: {e}")
        return None

def send_telegram(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload, timeout=10)

def main():
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        print("Telegram kimlik bilgileri eksik!")
        return

    mod = sys.argv[1] if len(sys.argv) > 1 else "bugun"
    now = datetime.now()

    if mod == "yarin":
        target = now + timedelta(days=1)
        baslik = "🌙 *Yarının Yemek Menüsü*"
    else:
        target = now
        baslik = "☀️ *Günün Yemek Menüsü*"

    if target.weekday() >= 5:
        print("Hedef gün hafta sonuna denk geliyor, bildirim gönderilmedi.")
        return

    items = get_menu_by_date(target)
    tarih_str = target.strftime("%d.%m.%Y")

    if items:
        mesaj = f"{baslik} ({tarih_str})\n\n"
        for it in items:
            mesaj += f"• {it}\n"
        send_telegram(bot_token, chat_id, mesaj)
        print("Telegram bildirimi başarıyla gönderildi.")
    else:
        print("Menü bulunamadı veya siteye erişilemedi.")

if __name__ == "__main__":
    main()
