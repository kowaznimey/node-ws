[app]
# (str) Title of your application
title = Ruijie Bypass Controller

# (str) Package name
package.name = ruijiebypass

# (str) Package domain (needed for android packaging)
package.domain = org.bypass

# (str) Source code directory
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas

# (str) Application version
version = 1.0.0

# (list) Application requirements
# Flet ၏ နောက်ကွယ်မှ Network နှင့် Cryptography လိုအပ်ချက်များကို အတိအကျ ဖြည့်သွင်းထားသည်
requirements = python3, flet, aiohttp, openssl, requests, charset-normalizer, idna, urllib3, hostpython3

# (list) Permissions
android.permissions = INTERNET, ACCESS_NETWORK_STATE, ACCESS_WIFI_STATE

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 24

# (str) Android NDK version to use
android.ndk = 25b

# (bool) Use private storage for data (True) or public (False)
android.private_storage = True

# (list) The Android architectures to build for
android.archs = arm64-v8a

# (list) Packaging options to prevent compression issues
android.no_compress = .py, .json, .png

# (int) Log level (2 = error only, 1 = info, 0 = debug)
log_level = 2

# (int) Give buildozer permissions to accept Android SDK licenses
android.accept_sdk_license = True
