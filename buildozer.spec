[app]

# Application info
title = PDF Reader
package.name = pdfreader
package.domain = com.app

# Source configuration
source.dir = src/huawei_pdf_reader
source.include_exts = py
source.include_patterns = main.py,__init__.py
source.exclude_dirs = tests,bin,venv,.git,__pycache__,ui
source.exclude_patterns = app.py,database.py,models.py,document_processor.py,annotation_engine.py,palm_rejection.py,file_manager.py,chinese_converter.py,translation_service.py,magnifier.py,plugin_manager.py,backup_service.py

# Version
version = 0.1.0

# Requirements - minimal and proven to work
requirements = python3,kivy==2.2.1,pillow

# Orientation
orientation = portrait

# Android configuration
fullscreen = 0
android.presplash_color = #1B5E20

# Permissions
android.permissions = INTERNET

# API levels - compatible with HarmonyOS
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21

# Accept SDK license
android.accept_sdk_license = True

# Architecture - arm64 for modern devices
android.archs = arm64-v8a

# AndroidX support
android.enable_androidx = True

# Storage
android.private_storage = True

# Backup
android.allow_backup = True

# Logcat
android.logcat_filters = *:S python:D

# Bootstrap - SDL2 is the default and most stable
# p4a.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 1
