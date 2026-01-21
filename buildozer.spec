[app]
title = Vibration Controller
package.name = vibecontroller
package.domain = it.crashando
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = python3,kivy==2.3.0,plyer,requests,certifi,urllib3,charset-normalizer,idna
orientation = portrait
fullscreen = 0

android.permissions = INTERNET,VIBRATE,WAKE_LOCK,FOREGROUND_SERVICE,POST_NOTIFICATIONS,FOREGROUND_SERVICE_SPECIAL_USE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a
android.gradle_dependencies = androidx.core:core:1.9.0
android.enable_androidx = True

services = VibrationService:service.py:foreground

android.presplash_color = #667eea

p4a.branch = master
p4a.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 1
