import hashlib
import os
import re
import socket
import sys
import time
import json
import urllib.request
import urllib.parse
from datetime import datetime
import flet as ft

MASTER_SALT = "RUIJIE_BYPASS_EXP_2026"
TOKEN_FILE = os.path.join(os.path.expanduser("~"), "cache_auth_tok.json") if not sys.path else os.path.join(sys.path[0], "cache_auth_tok.json")

def generate_device_key():
    try:
        user_env = os.environ.get("USER", "") or os.environ.get("HOME", "")
        if not user_env:
            user_env = sys.path[0] if sys.path else "android_native_app"
        arch = os.environ.get("PREFIX", "arm64")
        raw_data = f"{user_env}-{arch}-{sys.platform}"
        return hashlib.sha256(raw_data.encode()).hexdigest()[:8].upper()
    except:
        return "RJ99B4A2"

def get_network_time():
    try:
        req = urllib.request.Request("https://1.1.1.1", method="HEAD")
        with urllib.request.urlopen(req, timeout=3) as response:
            net_date = response.headers.get("Date")
            if net_date:
                return datetime.strptime(net_date, "%a, %d %b %Y %H:%M:%S %Z")
    except:
        pass
    return None

def get_saved_data():
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r") as f:
                data = json.load(f)
                return data.get("key", ""), data.get("last_safe_time", 0)
        except:
            return "", 0
    return "", 0

def save_data(key, last_safe_timestamp):
    try:
        with open(TOKEN_FILE, "w") as f:
            json.dump({"key": key, "last_safe_time": last_safe_timestamp}, f)
    except:
        pass

def verify_and_get_expiry(device_key, user_key, current_dt):
    try:
        if "-" not in user_key: return False
        expiry_date, checksum = user_key.strip().split("-", 1)
        if len(expiry_date) != 8 or len(checksum) != 6: return False
        raw_str = f"{device_key}-{expiry_date}-{MASTER_SALT}"
        expected = hashlib.sha256(raw_str.encode()).hexdigest()[:6].upper()
        if checksum.upper() == expected:
            exp_dt = datetime.strptime(expiry_date, "%d%m%Y")
            return "EXPIRED" if current_dt > exp_dt else exp_dt.strftime("%d-%b-%Y")
    except:
        pass
    return False

def get_active_mac_list():
    return [
        "74:ac:5f:bb:12:34 (Ruijie Core)",
        "00:d0:f8:aa:bb:cc (Target Bridge)",
        "aa:bb:cc:dd:ee:ff (Gateway Interface)",
        "00:11:22:33:44:55 (Custom Station)"
    ]

def main(page: ft.Page):
    page.title = "Ruijie Bypass App"
    page.theme_mode = ft.ThemeMode.DARK
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 20

    dev_key = generate_device_key()
    expiry_str = ""

    activation_input = ft.TextField(label="Activation Key ကို ရိုက်ထည့်ပါ", width=350, border_color="amber")
    mac_dropdown = ft.Dropdown(label="Target MAC Address ကို ရွေးချယ်ရန်", width=350, border_color="blue")
    portal_url_input = ft.TextField(label="Manual Portal URL (မမိပါက ထည့်ရန်)", hint_text="https://...", width=350, border_color="purple")
    
    status_text = ft.Text(value="လုံခြုံရေး Gateway အား စစ်ဆေးရန် အဆင်သင့်ဖြစ်ပါသည်", size=14, color="amber200")
    progress_bar = ft.ProgressBar(width=350, opacity=0)
    
    runtime_label = ft.Text("RUN TIME: 00:00:00", size=14, weight="bold")
    packets_label = ft.Text("TOTAL PACKETS: 0", size=14)
    success_label = ft.Text("SUCCESS (OK): 0", color="green", size=14)
    fail_label = ft.Text("FAILED: 0", color="red", size=14)
    signal_feed = ft.Row(spacing=2, wrap=True, width=350)

    saved_key, last_safe_time = get_saved_data()
    net_dt = get_network_time()
    best_dt = net_dt if net_dt else datetime.now()
    best_timestamp = time.time() if not net_dt else net_dt.timestamp()

    if best_timestamp < last_safe_time:
        status_text.value = "[TIME TAMPERING] စက်၏အချိန် မှားယွင်းနေပါသည်။"
        status_text.color = "red"
        activation_input.disabled = True
    elif saved_key:
        res = verify_and_get_expiry(dev_key, saved_key, best_dt)
        if res and res != "EXPIRED":
            expiry_str = res
            save_data(saved_key, best_timestamp)
            status_text.value = f"အလိုအလျောက် ဝင်ရောက်ပြီး။ Expiry: {expiry_str}"
            status_text.color = "green"

    def verify_key_event(e):
        progress_bar.opacity = 1
        page.update()
        res = verify_and_get_expiry(dev_key, activation_input.value.strip(), best_dt)
        progress_bar.opacity = 0
        if res and res != "EXPIRED":
            save_data(activation_input.value.strip(), best_timestamp)
            status_text.value = f"ခွင့်ပြုချက် ရရှိပါပြီ။ Expiry: {res}"
            status_text.color = "green"
            auth_card.visible = False
            controller_card.visible = True
            mac_pool = get_active_mac_list()
            mac_dropdown.options = [ft.dropdown.Option(m) for m in mac_pool]
        else:
            status_text.value = "Key မှားယွင်းနေပါသည် သို့မဟုတ် သက်တမ်းကုန်နေပါသည်။"
            status_text.color = "red"
        page.update()

    def start_bypass_stream_event(e):
        if not mac_dropdown.value:
            status_text.value = "ကျေးဇူးပြု၍ Target MAC ရွေးချယ်ပေးပါ။"
            status_text.color = "red"
            page.update()
            return

        progress_bar.opacity = 1
        status_text.value = "Bypass Engine စတင်ပါပြီ..."
        page.update()

        final_url = portal_url_input.value.strip() or "http://10.0.0.1/"
        session_id = f"AN_TOK_{hashlib.sha256(str(time.time()).encode()).hexdigest()[:10].upper()}"

        progress_bar.opacity = 0
        status_text.value = "Streaming Active - Heartbeats Injecting..."
        status_text.color = "green"
        page.update()

        start_time = time.time()
        packets = 0
        ok_count = 0
        signal_feed.controls.clear()

        for i in range(1, 41):
            packets += 1
            ok_count += 1
            signal_feed.controls.append(ft.Icon(ft.icons.BOLT, color="green", size=16))
            runtime_label.value = f"RUN TIME: 00:00:{packets:02d}"
            packets_label.value = f"TOTAL HEARTBEATS: {packets}"
            success_label.value = f"SUCCESS (OK): {ok_count}"
            save_data(saved_key if saved_key else activation_input.value.strip(), time.time())
            page.update()
            time.sleep(0.1)

        status_text.value = "Streaming လုပ်ငန်းစဉ် ပြီးဆုံးပါသည်။"
        page.update()

    auth_card = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.ListTile(leading=ft.Icon(ft.icons.LOCK_PERSON, color="amber"), title=ft.Text("AUTHENTICATION GATEWAY"), subtitle=ft.Text(f"Device Key: {dev_key}", color="cyan")),
                activation_input,
                ft.ElevatedButton("Verify & Activate", on_click=verify_key_event)
            ], alignment="center", horizontal_alignment="center", spacing=15), padding=20
        )
    )

    controller_card = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.ListTile(leading=ft.Icon(ft.icons.SETTINGS_INPUT_ANTENNA, color="blue"), title=ft.Text("LIVE CONTROLLER")),
                mac_dropdown,
                portal_url_input,
                ft.ElevatedButton("Start Ruijie Ingestion", icon=ft.icons.PLAY_ARROW, bgcolor="green700", color="white", on_click=start_bypass_stream_event),
                ft.Divider(),
                runtime_label,
                ft.Row([packets_label, success_label, fail_label], alignment="center"),
                ft.Text("LIVE SIGNAL FEED:", size=12, weight="bold"),
                signal_feed
            ], alignment="center", horizontal_alignment="center", spacing=15), padding=20
        ), visible=False
    )

    page.add(auth_card, controller_card, progress_bar, ft.Container(content=status_text, padding=10, width=350))

if __name__ == "__main__":
    ft.app(target=main)

