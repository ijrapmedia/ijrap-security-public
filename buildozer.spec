[app]

title = IJRAP Security Public
package.name = ijrappublic
package.domain = org.ijraplabs
source.dir = .
source.include_exts = py,png,jpg,kv,json,txt,csv,enc,ots
version = 1.0.0

requirements = python3,kivy==2.3.0,cryptography

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,CAMERA,RECORD_AUDIO,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION
android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a
android.allow_backup = False
android.accept_sdk_license = True

[buildozer]

log_level = 2
warn_on_root = 1


