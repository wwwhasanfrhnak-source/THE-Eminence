[app]
title = THE Eminence
package.name = theeminence
package.domain = org.theeminence
source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,atlas,ttf,db
source.include_patterns = assets/*
source.exclude_dirs = .venv,venv,tests,__pycache__
version = 1.0.0
requirements = python3,kivy==2.3.0,kivymd==1.2.0,pillow,arabic-reshaper,python-bidi,bcrypt
orientation = portrait
fullscreen = 0
presplash.filename = %(source.dir)s/assets/splash.png
icon.filename = %(source.dir)s/assets/icon.png
android.permissions =
android.api = 35
android.minapi = 23
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = False
android.private_storage = True
p4a.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 1
