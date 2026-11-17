#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 ADZE Kossivi Edem (IJRAP Media / IJRAP LABS)

import hashlib
import json
import os

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen

from ijrap_seal import IJRAPForensicSealer


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

<DangerButton@Button>:
    background_normal: ''
    background_color: 0.65, 0.15, 0.15, 1
    color: 1, 1, 1, 1
    bold: True

ScreenManager:
    SecurityScreen:
    VaultScreen:

<SecurityScreen>:
    name: 'login'
    BoxLayout:
        orientation: 'vertical'
        padding: '24dp'
        spacing: '14dp'
        Label:
            text: 'IJRAP LABS — PQC & SANDBOX CORE'
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
            text: 'Enter your session PIN'
            font_size: '13sp'
            color: 0.65, 0.70, 0.78, 1
            size_hint_y: 0.08
        GridLayout:
            cols: 3
            spacing: '10dp'
            size_hint_y: 0.65
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

<VaultScreen>:
    name: 'vault'
    BoxLayout:
        orientation: 'vertical'
        padding: '18dp'
        spacing: '10dp'
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: '34dp'
            Label:
                text: 'IN-MEMORY SEALING (PQC + AES)'
                bold: True
                color: 0.20, 0.78, 0.55, 1
                halign: 'left'
                text_size: self.size
            DangerButton:
                text: 'PANIC WIPE'
                size_hint_x: 0.35
                font_size: '12sp'
                on_press: root.trigger_panic_wipe()
        TextInput:
            id: title_input
            hint_text: 'Observation or evidence title'
            multiline: False
            size_hint_y: None
            height: '44dp'
        TextInput:
            id: note_input
            hint_text: 'Factual description to encrypt and sign...'
            multiline: True
            size_hint_y: 0.35
        AccentButton:
            text: 'SEAL & ENCRYPT (RAM -> VAULT)'
            size_hint_y: None
            height: '48dp'
            on_press: root.seal_note()
        Label:
            text: 'Chained certificates inside sandbox:'
            bold: True
            size_hint_y: None
            height: '26dp'
            halign: 'left'
            text_size: self.size
        ScrollView:
            Label:
                id: list_label
                text: 'No sealed records found.'
                size_hint_y: None
                height: self.texture_size[1]
                text_size: self.width, None
                halign: 'left'
"""


class SecurityScreen(Screen):
    entered_pin = StringProperty("")

    # Salted SHA-256 PIN hashes (1234 = normal mode, 9999 = duress mode)
    NORMAL_PIN_HASH = hashlib.sha256(b"IJRAP_SALT_2026:1234").hexdigest()
    DURESS_PIN_HASH = hashlib.sha256(b"IJRAP_SALT_2026:9999").hexdigest()

    def add_digit(self, digit: str):
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
        candidate_hash = hashlib.sha256(
            f"IJRAP_SALT_2026:{self.entered_pin}".encode("utf-8")
        ).hexdigest()

        if candidate_hash == self.NORMAL_PIN_HASH:
            app.duress_mode = False
            app.init_sealer(self.entered_pin)
            self.clear_pin()
            self.manager.current = "vault"
            app.refresh_list()
        elif candidate_hash == self.DURESS_PIN_HASH:
            app.duress_mode = True
            self.clear_pin()
            self.manager.current = "vault"
            app.refresh_list()
        else:
            self.ids.pin_hint.text = "INCORRECT PIN"
            self.clear_pin()


class VaultScreen(Screen):
    def seal_note(self):
        app = App.get_running_app()
        title = self.ids.title_input.text.strip()
        note = self.ids.note_input.text.strip()

        if not title or not note:
            Popup(
                title="Error",
                content=Label(text="Please fill in both title and report."),
                size_hint=(0.8, 0.3),
            ).open()
            return

        # In duress mode, simulate saving without writing anything to disk
        if app.duress_mode or app.sealer is None:
            self.ids.title_input.text = ""
            self.ids.note_input.text = ""
            return

        prev_hash = app.get_last_chain_hash()
        cert = app.sealer.seal_in_memory_bundle(
            title=title,
            written_report=note,
            previous_chain_hash=prev_hash,
            encryption_passphrase=app.session_secret,
            enable_opentimestamps=True,
        )

        self.ids.title_input.text = ""
        self.ids.note_input.text = ""
        app.refresh_list()

        Popup(
            title="Sealed & Encrypted in RAM",
            content=Label(
                text=(
                    f"UTC: {cert['timestamp_utc'][:19]}Z\n"
                    f"SHA3-512: {cert['sha3_512_digest'][:18]}...\n"
                    f"OTS: {cert['opentimestamps_proof']}"
                ),
                halign="center",
            ),
            size_hint=(0.88, 0.38),
        ).open()

    def trigger_panic_wipe(self):
        """Immediately wipes the local Ed25519 private key and locks the app."""
        app = App.get_running_app()
        if app.sealer:
            app.sealer.panic_wipe()
            app.sealer = None
            app.session_secret = ""
        self.manager.current = "login"
        Popup(
            title="Security Alert",
            content=Label(text="Private key wiped from sandbox."),
            size_hint=(0.8, 0.3),
        ).open()


class IJRAPSecurityApp(App):
    duress_mode = BooleanProperty(False)
    sealer = None
    session_secret = ""

    def build(self):
        self.title = "IJRAP Security Public"
        return Builder.load_string(KV_UI)

    def get_vault_dir(self) -> str:
        """Uses strictly the internal directory permitted by the mobile Sandbox."""
        vault = os.path.join(self.user_data_dir, "ijrap_vault")
        os.makedirs(vault, exist_ok=True)
        return vault

    def init_sealer(self, pin: str):
        self.session_secret = f"IJRAP_MASTER_{pin}"
        self.sealer = IJRAPForensicSealer(
            investigator_id="investigator_default",
            vault_dir=self.get_vault_dir(),
            key_passphrase=self.session_secret,
        )

    def get_last_chain_hash(self) -> str:
        vault = self.get_vault_dir()
        files = sorted([f for f in os.listdir(vault) if f.endswith(".json")])
        if not files:
            return "0" * 128
        try:
            with open(os.path.join(vault, files[-1]), "r", encoding="utf-8") as f:
                last_data = json.load(f)
                return last_data.get("sha3_512_digest", "0" * 128)
        except Exception:
            return "0" * 128

    def refresh_list(self):
        screen = self.root.get_screen("vault")
        if self.duress_mode:
            screen.ids.list_label.text = "No sealed records found."
            return
        files = sorted([f for f in os.listdir(self.get_vault_dir()) if f.endswith(".json")])
        screen.ids.list_label.text = (
            "\n".join(f"• {f}" for f in files) if files else "No sealed records found."
        )


if __name__ == "__main__":
    IJRAPSecurityApp().run()
