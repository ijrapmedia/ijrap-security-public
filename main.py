#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 ADZE Kossivi Edem (IJRAP Media / IJRAP LABS)

import os
import json
import uuid
from datetime import datetime, timezone
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import DictProperty, StringProperty, BooleanProperty
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.utils import platform

# Import sécurisé des modules Plyer et du module interne
try:
    from plyer import battery, camera, gps
except Exception:
    battery = camera = gps = None

try:
    from ijrap_public_sealer import IJRAPForensicSealer
except ImportError:
    IJRAPForensicSealer = None

# Fond sombre officiel (Dark Theme)
Window.clearcolor = (0.07, 0.08, 0.10, 1)

KV_UI = """
<DarkButton@Button>:
    background_normal: ''
    background_color: 0.16, 0.20, 0.27, 1
    color: 0.95, 0.96, 0.98, 1
    bold: True

<AccentButton@Button>:
    background_normal: ''
    background_color: 0.08, 0.55, 0.35, 1
    color: 1, 1, 1, 1
    bold: True

<DangerBanner@Label>:
    canvas.before:
        Color:
            rgba: 0.65, 0.12, 0.12, 1
        Rectangle:
            pos: self.pos
            size: self.size
    color: 1, 1, 1, 1
    bold: True
    size_hint_y: None
    height: '38dp'

ScreenManager:
    SecurityScreen:
    DashboardScreen:
    CaptureScreen:
    SynthesisScreen:

<SecurityScreen>:
    name: 'screen1'
    BoxLayout:
        orientation: 'vertical'
        padding: '24dp'
        spacing: '14dp'

        Label:
            text: 'IJRAP LABS — CITIZEN PUBLIC TIER'
            font_size: '20sp'
            bold: True
            color: 0.20, 0.78, 0.55, 1
            size_hint_y: 0.15

        Label:
            id: pin_display
            text: '[ _ ] [ _ ] [ _ ] [ _ ]'
            font_size: '26sp'
            bold: True
            size_hint_y: 0.12

        Label:
            id: pin_hint
            text: 'PIN Standard: 1234 | PIN Contrainte (Leurre): 9999'
            font_size: '12sp'
            color: 0.65, 0.70, 0.78, 1
            size_hint_y: 0.08

        GridLayout:
            cols: 3
            spacing: '10dp'
            size_hint_y: 0.55
            DarkButton:
                text: '1'
                on_press: root.add_digit('1')
            DarkButton:
                text: '2'
                on_press: root.add_digit('2')
            DarkButton:
                text: '3'
                on_press: root.add_digit('3')
            DarkButton:
                text: '4'
                on_press: root.add_digit('4')
            DarkButton:
                text: '5'
                on_press: root.add_digit('5')
            DarkButton:
                text: '6'
                on_press: root.add_digit('6')
            DarkButton:
                text: '7'
                on_press: root.add_digit('7')
            DarkButton:
                text: '8'
                on_press: root.add_digit('8')
            DarkButton:
                text: '9'
                on_press: root.add_digit('9')
            DarkButton:
                text: 'C'
                background_color: 0.55, 0.18, 0.18, 1
                on_press: root.clear_pin()
            DarkButton:
                text: '0'
                on_press: root.add_digit('0')
            AccentButton:
                text: 'OK'
                on_press: root.verify_pin()

<DashboardScreen>:
    name: 'screen2'
    BoxLayout:
        orientation: 'vertical'
        padding: '18dp'
        spacing: '10dp'

        Label:
            text: 'PROFIL & TABLEAU DE BORD (PUBLIC)'
            bold: True
            color: 0.20, 0.78, 0.55, 1
            size_hint_y: None
            height: '30dp'

        Label:
            id: inv_id_label
            text: 'ID Appareil: IJRAP-PUBLIC-001'
            size_hint_y: None
            height: '26dp'
            halign: 'left'
            text_size: self.size

        TextInput:
            id: alias_input
            hint_text: 'Nom ou Pseudonyme Protégé (Obligatoire)'
            multiline: False
            size_hint_y: None
            height: '42dp'

        TextInput:
            id: org_input
            hint_text: 'Statut (Citoyen, Journaliste, Observateur...)'
            multiline: False
            size_hint_y: None
            height: '42dp'

        Label:
            id: gps_status_label
            text: 'Statut: HORS LIGNE (Sécurisé) | GPS: En attente...'
            color: 0.65, 0.85, 0.70, 1
            size_hint_y: None
            height: '28dp'

        AccentButton:
            text: '+ NOUVELLE COLLECTE DE PREUVE'
            size_hint_y: None
            height: '48dp'
            on_press: root.start_new_investigation()

        Label:
            text: 'Preuves scellées localement (WORM 0o444):'
            bold: True
            size_hint_y: None
            height: '26dp'
            halign: 'left'
            text_size: self.size

        ScrollView:
            Label:
                id: bundles_list_label
                text: 'Aucun dossier scellé.'
                size_hint_y: None
                height: self.texture_size[1]
                text_size: self.width, None
                halign: 'left'

<CaptureScreen>:
    name: 'screen3'
    BoxLayout:
        orientation: 'vertical'
        padding: '18dp'
        spacing: '12dp'

        DangerBanner:
            text: 'CAPTURE EN DIRECT UNIQUEMENT (IMPORTATION GALERIE BLOQUÉE)'

        Label:
            text: 'ACQUISITION MATÉRIELLE SYNCHRONISÉE'
            bold: True
            color: 0.75, 0.80, 0.88, 1

        BoxLayout:
            orientation: 'horizontal'
            spacing: '8dp'
            size_hint_y: None
            height: '52dp'
            DarkButton:
                text: 'PHOTO'
                on_press: root.capture_media('photo')
            DarkButton:
                text: 'VIDÉO'
                on_press: root.capture_media('video')
            DarkButton:
                text: 'AUDIO'
                on_press: root.capture_media('audio')

        Label:
            id: streams_counter_label
            text: 'Flux capturés : Photo: 0 | Vidéo: 0 | Audio: 0'
            bold: True
            size_hint_y: None
            height: '36dp'

        Label:
            id: capture_log_label
            text: 'Prêt pour acquisition en direct.'
            color: 0.65, 0.75, 0.85, 1
            font_size: '13sp'

        BoxLayout:
            orientation: 'horizontal'
            spacing: '10dp'
            size_hint_y: None
            height: '48dp'
            DarkButton:
                text: '<- RETOUR'
                size_hint_x: 0.35
                on_press: root.manager.current = 'screen2'
            AccentButton:
                text: 'PASSER À LA SYNTHÈSE ->'
                size_hint_x: 0.65
                on_press: root.manager.current = 'screen4'

<SynthesisScreen>:
    name: 'screen4'
    BoxLayout:
        orientation: 'vertical'
        padding: '16dp'
        spacing: '10dp'

        Label:
            text: 'SYNTHÈSE & SCELLEMENT CRYPTOGRAPHIQUE'
            bold: True
            color: 0.20, 0.78, 0.55, 1
            size_hint_y: None
            height: '28dp'

        TextInput:
            id: title_input
            hint_text: "1. Titre de l'enquête ou de l'observation (Obligatoire)"
            multiline: False
            size_hint_y: None
            height: '42dp'

        Spinner:
            id: consent_mode_spinner
            text: 'Enquête AVEC consentement vérifié'
            values: ['Enquête AVEC consentement vérifié', 'Observation publique / SANS consentement']
            size_hint_y: None
            height: '44dp'
            on_text: root.on_consent_mode_change(self.text)

        BoxLayout:
            id: consent_box
            orientation: 'horizontal'
            size_hint_y: None
            height: '36dp'
            CheckBox:
                id: consent_checkbox
                size_hint_x: 0.15
                active: False
            Label:
                id: consent_label
                text: 'Je certifie avoir obtenu le consentement éclairé du témoin.'
                font_size: '13sp'
                halign: 'left'
                text_size: self.size

        TextInput:
            id: synthesis_input
            hint_text: '2. Récit factuel et synthèse de la preuve (Min. 50 caractères)...'
            multiline: True
            size_hint_y: 0.40

        TextInput:
            id: sources_input
            hint_text: '3. Références / Contexte additionnel (Optionnel)'
            multiline: False
            size_hint_y: None
            height: '42dp'

        BoxLayout:
            orientation: 'horizontal'
            spacing: '10dp'
            size_hint_y: None
            height: '48dp'
            DarkButton:
                text: '<- RETOUR'
                size_hint_x: 0.35
                on_press: root.manager.current = 'screen3'
            AccentButton:
                text: 'SCELLER LA PREUVE (SHA-256)'
                size_hint_x: 0.65
                on_press: root.seal_investigation()
"""


def show_alert(title, message):
    popup = Popup(
        title=title,
        content=Label(text=message, halign='center', valign='middle'),
        size_hint=(0.85, 0.35),
    )
    popup.open()


class SecurityScreen(Screen):
    entered_pin = StringProperty("")

    def add_digit(self, digit):
        if len(self.entered_pin) < 4:
            self.entered_pin += digit
            self.update_display()

    def clear_pin(self):
        self.entered_pin = ""
        self.update_display()

    def update_display(self):
        slots = [self.entered_pin[i] if i < len(self.entered_pin) else "_" for i in range(4)]

self.ids.pin_display.text = f"[ {slots[0]} ] [ {slots[1]} ] [ {slots[2]} ] [ {slots[3]} ]"
def verify_pin(self):
app = App.get_running_app()
if self.entered_pin == "1234":
app.duress_mode = False
self.clear_pin()
self.manager.current = "screen2"
app.refresh_dashboard()
elif self.entered_pin == "9999":
app.duress_mode = True
self.clear_pin()
self.manager.current = "screen2"
app.refresh_dashboard()
else:
self.ids.pin_hint.text = "CODE PIN INCORRECT — RÉESSAYEZ"
self.ids.pin_hint.color = (0.95, 0.30, 0.30, 1)
self.clear_pin()
class DashboardScreen(Screen):
def start_new_investigation(self):
alias = self.ids.alias_input.text.strip()
if not alias:
show_alert("Champ Requis", "Veuillez saisir un Nom ou Pseudonyme Protégé.")
return
app = App.get_running_app()
app.current_session = {
"session_id": str(uuid.uuid4()),
"alias": alias,
"role": self.ids.org_input.text.strip() or "Citoyen",
"started_at": datetime.now(timezone.utc).isoformat(),
"media": [],
"counts": {"photo": 0, "video": 0, "audio": 0},
}
self.manager.current = "screen3"
class CaptureScreen(Screen):
def capture_media(self, media_type):
app = App.get_running_app()
storage_dir = app.get_vault_dir()
filename = f"{media_type}_{uuid.uuid4().hex[:8]}"
if media_type == "photo":
filepath = os.path.join(storage_dir, f"{filename}.jpg")
if platform == "android" and camera:
try:
camera.take_picture(
filename=filepath,
on_complete=lambda path: self.on_media_captured("photo", path),
)
self.ids.capture_log_label.text = "Ouverture de la caméra sécurisée..."
return
except Exception as e:
self.ids.capture_log_label.text = f"Fallback capteur photo ({e})"
# Mode simulation / fallback bureau
with open(filepath, "wb") as f:
f.write(b"IJRAP_RAW_PHOTO_STREAM_" + os.urandom(32))
self.on_media_captured("photo", filepath)
elif media_type in ("video", "audio"):
ext = "mp4" if media_type == "video" else "wav"
filepath = os.path.join(storage_dir, f"{filename}.{ext}")
with open(filepath, "wb") as f:
f.write(f"IJRAP_RAW_{media_type.upper()}STREAM".encode() + os.urandom(64))
self.on_media_captured(media_type, filepath)
def on_media_captured(self, media_type, filepath):
app = App.get_running_app()
if filepath and os.path.exists(filepath):
app.current_session["media"].append({"type": media_type, "path": filepath})
app.current_session["counts"][media_type] += 1
c = app.current_session["counts"]
self.ids.streams_counter_label.text = (
f"Flux capturés : Photo: {c['photo']} | Vidéo: {c['video']} | Audio: {c['audio']}"
)
self.ids.capture_log_label.text = f"Flux {media_type.upper()} verrouillé en mémoire."
class SynthesisScreen(Screen):
def on_consent_mode_change(self, text):
is_consent_required = "AVEC" in text
self.ids.consent_checkbox.disabled = not is_consent_required
if not is_consent_required:
self.ids.consent_checkbox.active = False
def seal_investigation(self):
app = App.get_running_app()
title = self.ids.title_input.text.strip()
narrative = self.ids.synthesis_input.text.strip()
consent_mode = self.ids.consent_mode_spinner.text
if not title:
show_alert("Erreur", "Le titre de l'enquête est obligatoire.")
return
if "AVEC" in consent_mode and not self.ids.consent_checkbox.active:
show_alert("Consentement Requis", "Veuillez cocher la case de consentement éclairé.")
return
if len(narrative) < 50:
show_alert("Récit Trop Court", "La synthèse doit contenir au moins 50 caractères.")
return
payload = {
"session": app.current_session,
"title": title,
"consent_mode": consent_mode,
"narrative": narrative,
"sources": self.ids.sources_input.text.strip(),
"gps": app.gps_coords,
"sealed_at": datetime.now(timezone.utc).isoformat(),
}
if IJRAPForensicSealer:
sealer = IJRAPForensicSealer(vault_dir=app.get_vault_dir())
result = sealer.seal_bundle(payload)
bundle_hash = result.get("sha256", "SCELLE")
else:
import hashlib
raw = json.dumps(payload, sort_keys=True).encode("utf-8")
bundle_hash = hashlib.sha256(raw).hexdigest()
out_file = os.path.join(app.get_vault_dir(), f"IJRAP_{bundle_hash[:12]}.json")
with open(out_file, "w", encoding="utf-8") as f:
json.dump({"hash": bundle_hash, "payload": payload}, f, indent=2)
try:
os.chmod(out_file, 0o444)
except Exception:
pass
# Réinitialisation du formulaire et retour au tableau de bord
self.ids.title_input.text = ""
self.ids.synthesis_input.text = ""
self.ids.sources_input.text = ""
self.ids.consent_checkbox.active = False
show_alert("Preuve Scellée", f"Empreinte SHA-256 :\n{bundle_hash[:24]}...")
self.manager.current = "screen2"
app.refresh_dashboard()
class IJRAPApp(App):
duress_mode = BooleanProperty(False)
gps_coords = DictProperty({"lat": None, "lon": None})
current_session = DictProperty({})
def build(self):
self.title = "IJRAP Security Public"
return Builder.load_string(KV_UI)
def on_start(self):
if platform == "android":
from android.permissions import Permission, request_permissions
request_permissions(
[
Permission.CAMERA,
Permission.RECORD_AUDIO,
Permission.ACCESS_FINE_LOCATION,
Permission.ACCESS_COARSE_LOCATION,
Permission.READ_EXTERNAL_STORAGE,
Permission.WRITE_EXTERNAL_STORAGE,
],
self.on_permissions_result,
)
else:
self.start_gps()
def on_permissions_result(self, permissions, grants):
self.start_gps()
def start_gps(self):
if gps:
try:
gps.configure(on_location=self.on_gps_location, on_status=self.on_gps_status)
gps.start(minTime=5000, minDistance=5)
except Exception:
pass
def on_gps_location(self, **kwargs):
self.gps_coords = {"lat": kwargs.get("lat"), "lon": kwargs.get("lon")}
screen2 = self.root.get_screen("screen2")
screen2.ids.gps_status_label.text = (
f"Statut: HORS LIGNE | GPS: {self.gps_coords['lat']:.4f}, {self.gps_coords['lon']:.4f}"
)
def on_gps_status(self, stype, status):
pass
def get_vault_dir(self):
base = self.user_data_dir
vault = os.path.join(base, "ijrap_vault")
os.makedirs(vault, exist_ok=True)
return vault
def refresh_dashboard(self):
screen2 = self.root.get_screen("screen2")
if self.duress_mode:
screen2.ids.bundles_list_label.text = "Aucun dossier scellé."
return
vault = self.get_vault_dir()
files = sorted([f for f in os.listdir(vault) if f.endswith(".json")])
if not files:
screen2.ids.bundles_list_label.text = "Aucun dossier scellé."
else:
screen2.ids.bundles_list_label.text = "\n".join(f"• {f}" for f in files)
if name == "main":
IJRAPApp().run()
