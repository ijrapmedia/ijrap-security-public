[app]
title = IJRAP Security Public
package.name = ijrappublic
package.domain = org.ijraplabs
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,txt
version = 1.0.0

# Dépendances exactes pour Android (ajout de pyjnius indispensable pour plyer)
requirements = python3,kivy==2.3.0,plyer,pyjnius

orientation = portrait
fullscreen = 0

# Permissions matérielles requises (compatibles Android 7 à 13+)
android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,CAMERA,RECORD_AUDIO,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,READ_MEDIA_IMAGES,READ_MEDIA_VIDEO,READ_MEDIA_AUDIO
android.api = 33
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = False

# Recommandé pour éviter les erreurs de compilation Gradle récentes
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
