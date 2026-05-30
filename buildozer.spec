[app]

# --- App Identity ---
title = MyMusic
package.name = mymusic
package.domain = com.private.mymusic

# --- Source ---
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,json,txt
source.exclude_dirs = tests, bin, .buildozer

# --- Version ---
version = 1.0

# --- Dependencies ---
# All free, open-source Python libraries
requirements = python3,kivy==2.2.1,kivymd==1.1.1,requests,certifi,charset-normalizer,idna,urllib3,yt-dlp,ytmusicapi,pyjnius,android

# --- Display ---
orientation = portrait
fullscreen = 0

# --- Android Permissions ---
android.permissions = INTERNET, WAKE_LOCK, FOREGROUND_SERVICE, FOREGROUND_SERVICE_MEDIA_PLAYBACK, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# --- Android SDK/NDK ---
android.api = 33
android.minapi = 24
android.ndk = 25b
android.sdk = 33
android.ndk_api = 24
android.accept_sdk_license = True

# --- Build for modern and older phones ---
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1
