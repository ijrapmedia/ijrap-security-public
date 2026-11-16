#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 ADZE Kossivi Edem (IJRAP Media / IJRAP LABS)

import hashlib
import json
import os
import secrets
import time
import uuid
from datetime import datetime, timezone
from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen

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
            text: 'IJRAP LABS — PQC & HORODATAGE'
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
            text: 'PIN Test: 1234 | PIN Leurre: 9999'
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

        Label:
            text: 'SCELLEMENT POST-QUANTIQUE (SHA3-512)'
            bold: True
            color: 0.20, 0.78, 0.55, 1
            size_hint_y: None
            height: '30dp'

        TextInput:
            id: title_input
            hint_text: "Titre de l'observation ou preuve"
            multiline: False
            size_hint_y: None
            height: '44dp'

        TextInput:
            id: note_input
            hint_text: 'Description factuelle à horodater et signer...'
            multiline: True
            size_hint_y: 0.35

        AccentButton:
            text: 'SCELLER (PQC + HORODATAGE CHAÎNÉ)'
            size_hint_y: None
            height: '48dp'
            on_press: root.seal_note()

        Label:
            text: 'Registre immuable local (WORM 0o444) :'
            bold: True
            size_hint_y: None
            height: '26dp'
            halign: 'left'
            text_size: self.size

        ScrollView:
            Label:
                id: list_label
                text: 'Aucun dossier scellé.'
                size_hint_y: None
                height: self.texture_size[1]
                text_size: self.width, None
                halign: 'left'
"""


class PostQuantumLamportSigner:
    """Signature Post-Quantique basée sur le hachage (Lamport-SHA3-512)."""

    @staticmethod
    def sign_digest(digest_bytes: bytes) -> dict:
        # Génère une paire de clés éphémères 256 bits x 2 x 32 octets
        sk_0 = [secrets.token_bytes(32) for _ in range(256)]
        sk_1 = [secrets.token_bytes(32) for _ in range(256)]

        pk_0 = [hashlib.sha3_512(k).hexdigest() for k in sk_0]
        pk_1 = [hashlib.sha3_512(k).hexdigest() for k in sk_1]

        bits = "".join(f"{byte:08b}" for byte in digest_bytes[:32])
        signature = [
            sk_1[i].hex() if bit == "1" else sk_0[i].hex()
            for i, bit in enumerate(bits)
        ]

        pk_root = hashlib.sha3_512(
            "".join(pk_0 + pk_1).encode("utf-8")
        ).hexdigest()

        return {
            "algorithm": "LAMPORT-OTS-SHA3-512 (NIST-PQC-HASH-BASED)",
            "public_key_root": pk_root,
            "signature_preview": hashlib.sha3_512("".join(signature).encode()).hexdigest(),
            "signature_vectors": signature,
        }


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
            self.manager.current = "vault"
            app.refresh_list()
        elif self.entered_pin == "9999":
            app.duress_mode = True
            self.clear_pin()
            self.manager.current = "vault"
            app.refresh_list()
        else:
            self.ids.pin_hint.text = "PIN INCORRECT"
            self.clear_pin()


class VaultScreen(Screen):
    def seal_note(self):
        app = App.get_running_app()
        title = self.ids.title_input.text.strip()
        note = self.ids.note_input.text.strip()

        if not title or not note:
            Popup(
                title="Erreur",
                content=Label(text="Remplissez le titre et le récit."),
                size_hint=(0.8, 0.3),
            ).open()
            return

        # 1. Horodatage double (UTC ISO-8601 + Monotone anti-retour arrière)
        now_utc = datetime.now(timezone.utc)
        timestamp_iso = now_utc.isoformat()
        monotonic_ns = time.monotonic_ns()
        prev_hash = app.get_last_chain_hash()

        payload = {
            "bundle_id": str(uuid.uuid4()),
            "title": title,
            "note": note,
            "timestamp_utc": timestamp_iso,
            "monotonic_clock_ns": monotonic_ns,
            "previous_chain_hash": prev_hash,
        }

        # 2. Empreinte Post-Quantique SHA3-512
        canonical_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        pqc_digest = hashlib.sha3_512(canonical_bytes).digest()
        pqc_hex = pqc_digest.hex()

        # 3. Signature Post-Quantique Lamport-SHA3-512
        pqc_signature = PostQuantumLamportSigner.sign_digest(pqc_digest)

        sealed_record = {
            "schema": "IJRAP-PQC-CHAIN-v1",
            "sha3_512_digest": pqc_hex,
            "payload": payload,
            "post_quantum_signature": pqc_signature,
        }

        filename = f"IJRAP_{now_utc.strftime('%Y%m%dT%H%M%SZ')}_{pqc_hex[:10]}.json"
        filepath = os.path.join(app.get_vault_dir(), filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(sealed_record, f, indent=2)

        try:
            os.chmod(filepath, 0o444)
        except Exception:
            pass

        self.ids.title_input.text = ""
        self.ids.note_input.text = ""
        Popup(
            title="Scellé Post-Quantique",
            content=Label(
                text=f"UTC: {timestamp_iso[:19]}Z\nSHA3-512: {pqc_hex[:18]}...\nChaîne liée: {prev_hash[:12]}...",
                halign="center",
            ),
            size_hint=(0.88, 0.38),
        ).open()
        app.refresh_list()


class IJRAPTestApp(App):
    duress_mode = BooleanProperty(False)

    def build(self):
        self.title = "IJRAP Security Public"
        return Builder.load_string(KV_UI)

    def get_vault_dir(self):
        vault = os.path.join(self.user_data_dir, "ijrap_vault")
        os.makedirs(vault, exist_ok=True)
        return vault

    def get_last_chain_hash(self):
        vault = self.get_vault_dir()
        files = sorted([f for f in os.listdir(vault) if f.endswith(".json")])
        if not files:
            return "0" * 128  # Bloc Genesis SHA3-512
        try:
            with open(os.path.join(vault, files[-1]), "r", encoding="utf-8") as f:
                last_data = json.load(f)
                return last_data.get("sha3_512_digest", "0" * 128)
        except Exception:
            return "0" * 128

    def refresh_list(self):
        screen = self.root.get_screen("vault")
        if self.duress_mode:
            screen.ids.list_label.text = "Aucun dossier scellé."
            return
        files = sorted([f for f in os.listdir(self.get_vault_dir()) if f.endswith(".json")])
        screen.ids.list_label.text = "\n".join(f"• {f}" for f in files) if files else "Aucun dossier scellé."


if __name__ == "__main__":
    IJRAPTestApp().run()
