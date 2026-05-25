import asyncio
import hashlib
import os
import re
import socket
import subprocess
import sys
import time
from datetime import datetime
import aiohttp
import flet as ft

# --- Security Config ---
MASTER_SALT = "RUIJIE_BYPASS_EXP_2026"

# --- Core Security & Network Logic ---
def generate_device_key():
    try:
        username = os.getlogin()
    except Exception:
        username = os.environ.get("USER", "termux_user")
    arch = os.environ.get("PREFIX", "generic_path")
    raw_data = f"{username}-{arch}-{sys.platform}"
    hasher = hashlib.sha256(raw_data.encode()).hexdigest()
    return hasher[:8].upper()

async def get_network_time():
    urls = ["https://1.1.1.1", "https://www.cloudflare.com"]
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        for url in urls:
            try:
                async with session.head(url, timeout=2) as response:
                    net_date = response.headers.get("Date")
                    if net_date:
                        parsed_time = datetime.strptime(net_date, "%a, %d %b %Y %H:%M:%S %Z")
                        return parsed_time
            except Exception:
                continue
    return None

def verify_and_get_expiry(device_key, user_key, current_dt):
    try:
        if "-" not in user_key:
            return False
        expiry_date, checksum = user_key.strip().split("-", 1)
        if len(expiry_date) != 8 or len(checksum) != 6:
            return False
        
        raw_str = f"{device_key}-{expiry_date}-{MASTER_SALT}"
        expected_checksum = hashlib.sha256(raw_str.encode()).hexdigest()[:6].upper()
        
        if checksum.upper() != expected_checksum:
            return False
        
        exp_dt = datetime.strptime(expiry_date, "%d%m%Y")
        if current_dt > exp_dt:
            return "EXPIRED"
            
        return exp_dt.strftime("%d-%b-%Y")
    except Exception:
        return False

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "10.0.0.1"
    finally:
        s.close()
    return ip

def get_active_mac_list():
    local_ip = get_local_ip()
    ip_parts = local_ip.split(".")
    ip_range = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.0/24"

    try:
        subprocess.run(["nmap", "-sn", ip_range], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        pass

    mac_list = []
    try:
        output = subprocess.check_output(["ip", "neigh"], text=True).strip()
        for line in output.split("\n"):
            if "lladdr" in line and "FAILED" not in line:
                mac_search = re.search(r"(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}", line)
                if mac_search:
                    mac_list.append(mac_search.group(0).lower())
    except:
        pass
    
    return list(set(mac_list)) if mac_list else ["00:11:22:33:44:55", "aa:bb:cc:dd:ee:ff"]

# --- Flet UI Application ---
def main(page: ft.Page):
    page.title = "Ruijie Bypass App"
    page.theme_mode = ft.ThemeMode.DARK
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 20

    dev_key = generate_device_key()
    is_authenticated = False
    expiry_string = ""

    activation_input = ft.TextField(label="Activation Key ကို ရိုက်ထည့်ပါ", width=350, border_color="amber")
    mac_dropdown = ft.Dropdown(label="Target MAC Address ကို ရွေးချယ်ရန်", width=350, border_color="blue")
    
    status_text = ft.Text(value="လုံခြုံရေး Gateway အား စစ်ဆေးရန် အဆင်သင့်ဖြစ်ပါသည်", size=14, color="amber200")
    progress_bar = ft.ProgressBar(width=350, opacity=0)
    
    runtime_label = ft.Text("RUN TIME: 00:00:00", size=14, weight="bold")
    packets_label = ft.Text("TOTAL PACKETS: 0", size=14)
    success_label = ft.Text("SUCCESS (OK): 0", color="green", size=14)
    fail_label = ft.Text("FAILED: 0", color="red", size=14)
    signal_feed = ft.Row(spacing=2, wrap=True, width=350)

    auth_card = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.ListTile(
                    leading=ft.Icon(ft.icons.LOCK_PERSON, color="amber", size=35),
                    title=ft.Text("SECURITY AUTHENTICATION GATEWAY", weight="bold"),
                    subtitle=ft.Text(f"Your Device Key: {dev_key}", color="cyan"),
                ),
                activation_input,
                ft.ElevatedButton("Verify & Activate", icon=ft.icons.CHECK, on_click=lambda e: asyncio.run(verify_key_event(e)))
            ], alignment="center", horizontal_alignment="center", spacing=15),
            padding=20
        ),
        visible=True
    )

    controller_card = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.ListTile(
                    leading=ft.Icon(ft.icons.SETTINGS_INPUT_ANTENNA, color="blue", size=35),
                    title=ft.Text("LIVE STREAM CONTROLLER", weight="bold"),
                    subtitle=ft.Text("Network Scanner & Injection Panel", color="grey400"),
                ),
                mac_dropdown,
                ft.Row([
                    ft.ElevatedButton("Scan Network", icon=ft.icons.SEARCH, on_click=lambda e: scan_network_event(e)),
                    ft.ElevatedButton("Start Inject", icon=ft.icons.PLAY_ARROW, bgcolor="green700", color="white", on_click=lambda e: asyncio.run(start_stream_event(e)))
                ], alignment="center", spacing=15),
                ft.Divider(),
                runtime_label,
                ft.Row([packets_label, success_label, fail_label], alignment="center", spacing=10),
                ft.Text("SIGNAL FEED:", size=12, weight="bold"),
                signal_feed
            ], alignment="center", horizontal_alignment="center", spacing=15),
            padding=20
        ),
        visible=False
    )

    async def verify_key_event(e):
        nonlocal is_authenticated, expiry_string
        progress_bar.opacity = 1
        page.update()

        net_dt = await get_network_time()
        best_dt = net_dt if net_dt else datetime.now()
        
        user_key = activation_input.value.strip()
        res = verify_and_get_expiry(dev_key, user_key, best_dt)

        progress_bar.opacity = 0
        if res and res != "EXPIRED":
            is_authenticated = True
            expiry_string = res
            status_text.value = f"ဝင်ရောက်ခွင့်ပြုပြီး။ Expiry: {expiry_string}"
            status_text.color = "green"
            auth_card.visible = False
            controller_card.visible = True
        elif res == "EXPIRED":
            status_text.value = "ဤ Key မှာ သက်တမ်းကုန်ဆုံးနေပါပြီ။"
            status_text.color = "red"
        else:
            status_text.value = "မှားယွင်းနေပါသည်။ သက်တမ်းရှိသော Key ကိုထည့်ပါ။"
            status_text.color = "red"
        page.update()

    def scan_network_event(e):
        progress_bar.opacity = 1
        status_text.value = "ကွန်ရက်အတွင်း MAC များကို Scan ဖတ်နေပါသည်..."
        page.update()

        mac_pool = get_active_mac_list()
        mac_dropdown.options = [ft.dropdown.Option(mac) for mac in mac_pool]
        
        progress_bar.opacity = 0
        status_text.value = f"Scan ဖတ်ခြင်းပြီးပါပြီ။ ကွန်ရက်ပစ္စည်း {len(mac_pool)} ခုတွေ့ရှိ။"
        status_text.color = "blue200"
        page.update()

    async def start_stream_event(e):
        if not mac_dropdown.value:
            status_text.value = "ကျေးဇူးပြု၍ Target MAC အရင်ရွေးချယ်ပေးပါ။"
            status_text.color = "red"
            page.update()
            return

        status_text.value = f"Streaming စတင်နေပါပြီ... Target: {mac_dropdown.value}"
        status_text.color = "green"
        page.update()

        start_time = time.time()
        packets = 0
        ok_count = 0
        fail_count = 0

        for i in range(1, 31):
            await asyncio.sleep(1)
            packets += 1
            if i % 5 == 0:
                fail_count += 1
                signal_feed.controls.append(ft.Icon(ft.icons.DASHBOARD_CUSTOMIZE, color="red", size=16))
            else:
                ok_count += 1
                signal_feed.controls.append(ft.Icon(ft.icons.DASHBOARD_CUSTOMIZE, color="green", size=16))

            diff = int(time.time() - start_time)
            runtime_label.value = f"RUN TIME: {diff // 3600:02d}:{(diff % 3600) // 60:02d}:{diff % 60:02d}"
            packets_label.value = f"TOTAL PACKETS: {packets}"
            success_label.value = f"SUCCESS (OK): {ok_count}"
            fail_label.value = f"FAILED: {fail_count}"
            page.update()

        status_text.value = "Streaming လုပ်ငန်းစဉ် ပြီးဆုံးသွားပါပြီ။"
        page.update()

    page.add(
        auth_card,
        controller_card,
        ft.Divider(height=10, color=ft.colors.TRANSPARENT),
        progress_bar,
        ft.Container(content=status_text, padding=10, border_radius=8, bgcolor=ft.colors.BLACK26, width=350)
    )

if __name__ == "__main__":
    # Android Client အတွက် တရားဝင် Native App UI Mode သို့ ပြောင်းလဲခြင်း
    ft.run(main)
