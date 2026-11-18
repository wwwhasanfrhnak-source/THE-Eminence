[app]
title = ElectroCalc
package.name = app
package.domain = com.electrocalc
source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,atlas,ttf,db
source.include_patterns = assets/*
source.exclude_dirs = .venv,venv,tests,__pycache__,bin,.buildozer
version = 1.0.0
requirements = python3,kivy==2.3.0,kivymd==1.2.0,asynckivy,asyncgui,pillow,arabic-reshaper,six,python-bidi==0.4.2,bcrypt,certifi
orientation = portrait
fullscreen = 0
presplash.filename = %(source.dir)s/assets/splash.png
icon.filename = %(source.dir)s/assets/icon.png
android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE
android.extra_manifest_application_arguments = android-extra-manifest-application-arguments.xml
android.api = 34
android.minapi = 23
android.ndk = 25b
android.archs = arm64-v8a
android.allow_backup = False
android.release_artifact = apk
android.private_storage = True
android.accept_sdk_license = True
p4a.bootstrap = sdl2
p4a.branch = v2024.01.21
p4a.commit = v2024.01.21

[buildozer]
log_level = 2
warn_on_root = 1
