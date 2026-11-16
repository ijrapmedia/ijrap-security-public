[app]
title = IJRAP Security Public
package.name = ijrappublic
package.domain = org.ijraplabs
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,txt
version = 1.0.0

# Dépendances exactes pour Android
requirements = python3,kivy==2.3.0,plyer

orientation = portrait
fullscreen = 0

# Permissions matérielles requises sur Android
android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,CAMERA,RECORD_AUDIO,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = False

[buildozer]
log_level = 2
warn_on_root = 1
