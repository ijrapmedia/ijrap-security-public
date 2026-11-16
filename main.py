#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 ADZE Kossivi Edem (IJRAP Media / IJRAP LABS)

import os
import uuid
from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import DictProperty, StringProperty
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.utils import platform
from plyer import battery, camera, gps
from ijrap_public_sealer import IJRAPForensicSealer

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
            hint_text: '2. Récit factuel et synthèse de la preuve (Min. 50 caractères pour essai)...'
            multiline: True
            size_hint_y: 0.45

        TextInput:
            id: sources_input
            hint_text: '3. Contexte, lieu précis ou notes complémentaires...'
            multiline: True
            size_hint_y: 0.20

        Label:
            id: seal_feedback
            text: ''
            color: 0.95, 0.75, 0.20, 1
            size_hint_y: None
            height: '24dp'

        BoxLayout:
            orientation: 'horizontal'
            spacing: '10dp'
            size_hint_y: None
            height: '48dp'
            DarkButton:
                text: '<- CAPTURE'
                size_hint_x: 0.3
                on_press: root.manager.current = 'screen3'
            AccentButton:
                text: 'SCELLER (SHA-256 + SHA3-256)'
                size_hint_x: 0.7
                on_press: root.execute_seal()
"""


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
        elif self.entered_pin == "9999":
            app.duress_mode = True
            app.captured_streams = {}
            self.clear_pin()
            self.manager.current = "screen2"
        else:
            self.ids.pin_hint.text = "PIN INVALIDE. Utilisez 1234 ou 9999."
            self.clear_pin()

class DashboardScreen(Screen):
def on_enter(self):
app = App.get_running_app()
self.ids.inv_id_label.text = f"ID Appareil : {app.investigator_id}"
self.ids.gps_status_label.text = f"Statut: HORS LIGNE | GPS: {app.gps_coords[0]}, {app.gps_coords[1]}"
self.refresh_bundles()
def refresh_bundles(self):
app = App.get_running_app()
if app.duress_mode:
self.ids.bundles_list_label.text = "Aucun dossier scellé (Mode Sécurisé)."
return
files = [f for f in os.listdir(app.vault_dir) if f.endswith(".ijrap_bundle_seal.json")]
if not files:
self.ids.bundles_list_label.text = "Aucun dossier scellé pour le moment."
else:
self.ids.bundles_list_label.text = "\n".join([f"• {fn} [SEALED]" for fn in sorted(files)])
def start_new_investigation(self):
app = App.get_running_app()
alias = self.ids.alias_input.text.strip()
org = self.ids.org_input.text.strip()
if not alias or not org:
self.ids.gps_status_label.text = "ERREUR : Renseignez votre Nom/Alias et votre Statut."
return
app.current_session = {
"investigator_name_or_alias": alias,
"investigator_role_organization": org,
"bundle_id": f"PUBLIC_TEST_{uuid.uuid4().hex[:8].upper()}",
}
app.captured_streams = {}
self.manager.current = "screen3"
class CaptureScreen(Screen):
def on_enter(self):
self.update_counter()
def update_counter(self):
app = App.get_running_app()
p = 1 if "photo" in app.captured_streams else 0
v = 1 if "video" in app.captured_streams else 0
a = 1 if "audio" in app.captured_streams else 0
self.ids.streams_counter_label.text = f"Flux capturés : Photo: {p} | Vidéo: {v} | Audio: {a}"
def capture_media(self, media_type):
app = App.get_running_app()
ext = {"photo": "jpg", "video": "mp4", "audio": "wav"}[media_type]
filepath = os.path.join(app.vault_dir, f"{app.current_session['bundle_id']}_{media_type}.{ext}")
try:
if media_type == "photo" and platform in ("android", "ios"):
camera.take_picture(filename=filepath, on_complete=lambda p: self._register_stream(media_type, p))
return
except Exception:
pass
with open(filepath, "wb") as f:
f.write(f"IJRAP_PUBLIC_LIVE_STREAM_{media_type.upper()}_{uuid.uuid4()}".encode("utf-8"))
self._register_stream(media_type, filepath)
def _register_stream(self, media_type, filepath):
if filepath and os.path.exists(filepath):
App.get_running_app().captured_streams[media_type] = filepath
self.update_counter()
class SynthesisScreen(Screen):
def on_consent_mode_change(self, mode_text):
if "AVEC" in mode_text:
self.ids.consent_checkbox.disabled = False
self.ids.consent_label.text = "Je certifie avoir obtenu le consentement éclairé du témoin."
else:
self.ids.consent_checkbox.active = False
self.ids.consent_checkbox.disabled = True
self.ids.consent_label.text = "Mode sans consentement (Observation publique / Test terrain)."
def execute_seal(self):
app = App.get_running_app()
title = self.ids.title_input.text.strip()
synthesis = self.ids.synthesis_input.text.strip()
sources = self.ids.sources_input.text.strip()
consent_mode = self.ids.consent_mode_spinner.text
with_consent = "AVEC" in consent_mode
if not title:
self.ids.seal_feedback.text = "ERREUR : Le titre est obligatoire."
return
if with_consent and not self.ids.consent_checkbox.active:
self.ids.seal_feedback.text = "ERREUR : Cochez la case de consentement ou passez en mode SANS consentement."
return
if len(synthesis) < 50:
self.ids.seal_feedback.text = f"ERREUR : Récit trop court ({len(synthesis)}/50 caractères min.)."
return
full_report = (
f"TITLE: {title}\n"
f"TIER: IJRAP Citizen Public\n"
f"CONSENT_STATUS: {consent_mode} (Verified={self.ids.consent_checkbox.active})\n"
f"INVESTIGATOR: {app.current_session['investigator_name_or_alias']} ({app.current_session['investigator_role_organization']})\n"
f"NOTES: {sources}\n"
f"SYNTHESIS: {synthesis}"
)
bundle_id = app.current_session["bundle_id"]
text_path = os.path.join(app.vault_dir, f"{bundle_id}_synthesis.txt")
with open(text_path, "w", encoding="utf-8") as f:
f.write(full_report)
streams = dict(app.captured_streams)
streams["written_pillar"] = text_path
try:
bat = int(battery.status.get("percentage", -1))
except Exception:
bat = -1
app.sealer.seal_synchronized_bundle(
bundle_id=bundle_id,
media_streams=streams,
gps_coords=app.gps_coords,
written_report=full_report,
battery_level=bat,
)
self.ids.title_input.text = ""
self.ids.synthesis_input.text = ""
self.ids.sources_input.text = ""
self.ids.consent_checkbox.active = False
self.ids.seal_feedback.text = ""
self.manager.current = "screen2"
class IJRAPCitizenPublicApp(App):
investigator_id = "IJRAP-PUBLIC-001"
duress_mode = False
current_session = DictProperty({})
captured_streams = DictProperty({})
gps_coords = (6.1375, 1.2123)
def build(self):
self.title = "IJRAP Security — Public Tier"
self.vault_dir = os.path.join(self.user_data_dir, "ijrap_public_vault")
self.sealer = IJRAPForensicSealer(
investigator_id=self.investigator_id,
storage_dir=self.vault_dir,
)
return Builder.load_string(KV_UI)
def on_start(self):
if platform == "android":
from android.permissions import Permission, request_permissions
request_permissions([
Permission.CAMERA,
Permission.RECORD_AUDIO,
Permission.ACCESS_FINE_LOCATION,
Permission.WRITE_EXTERNAL_STORAGE,
Permission.READ_EXTERNAL_STORAGE,
])
try:
gps.configure(on_location=self._on_gps_location)
gps.start(minTime=1000, minDistance=1)
except Exception:
pass
def _on_gps_location(self, **kwargs):
lat = kwargs.get("lat")
lon = kwargs.get("lon")
if lat is not None and lon is not None:
self.gps_coords = (round(float(lat), 6), round(float(lon), 6))
if name == "main":
IJRAPCitizenPublicApp().run()




