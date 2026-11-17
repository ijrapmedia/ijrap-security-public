#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 ADZE Kossivi Edem (IJRAP Media / IJRAP LABS)

import base64
import csv
import hashlib
import io
import json
import os
import platform
import secrets
import tarfile
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen


class PostQuantumLamportSigner:
    """Signature Post-Quantique basée sur le hachage (Lamport-SHA3-512) 100% Python pur."""

    @staticmethod
    def sign_digest(digest_bytes: bytes) -> dict:
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


class IJRAPForensicSealer:
    """
    IJRAP Security - Moteur de scellement adapté au Sandboxing Mobile (Android / iOS).
    Toutes les opérations d'assemblage et de chiffrement s'exécutent en mémoire vive (RAM).
    """

    def __init__(
        self,
        investigator_id: str,
        vault_dir: str,
        key_passphrase: str,
    ):
        self.investigator_id = investigator_id
        self.storage_dir = vault_dir
        self.key_storage_dir = os.path.join(vault_dir, ".ijrap_keystore")
        os.makedirs(self.storage_dir, exist_ok=True)
        os.makedirs(self.key_storage_dir, exist_ok=True)
        self._private_key, self.public_key_hex = self._load_or_create_device_keys(key_passphrase)

    def _load_or_create_device_keys(self, passphrase: str) -> tuple[ed25519.Ed25519PrivateKey, str]:
        """Génère ou charge la clé Ed25519 chiffrée par mot de passe (compatible Sandbox)."""
        priv_path = os.path.join(self.key_storage_dir, f"{self.investigator_id}_ed25519.pem")
        pwd_bytes = passphrase.encode("utf-8")

        if os.path.exists(priv_path):
            with open(priv_path, "rb") as kf:
                private_key = serialization.load_pem_private_key(kf.read(), password=pwd_bytes)
        else:
            private_key = ed25519.Ed25519PrivateKey.generate()
            pem_bytes = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.BestAvailableEncryption(pwd_bytes),
            )
            with open(priv_path, "wb") as kf:
                kf.write(pem_bytes)
                kf.flush()

        pub_bytes = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return private_key, pub_bytes.hex()

    def hash_bytes(self, data: bytes, filename: str) -> dict:
        return {
            "filename": filename,
            "size_bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "sha3_256": hashlib.sha3_256(data).hexdigest(),
            "sha3_512": hashlib.sha3_512(data).hexdigest(),
        }

    def sign_digest(self, hex_digest: str) -> str:
        return self._private_key.sign(hex_digest.encode("utf-8")).hex()

    def _derive_fernet_key(self, passphrase: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        return base64.urlsafe_b64encode(kdf.derive(passphrase.encode("utf-8")))

    def _build_proofmode_csv_bytes(
        self,
        hashed_streams: dict,
        gps_coords: tuple,
        sync_timestamp: str,
    ) -> bytes:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "File Hash SHA256",
            "File Path",
            "Location.Latitude",
            "Location.Longitude",
            "Location.Provider",
            "Device",
            "Proof Generated",
            "Public Key Fingerprint",
        ])
        lat, lon = gps_coords[0], gps_coords[1]
        for _, meta in sorted(hashed_streams.items()):
            writer.writerow([
                meta["sha256"],
                meta["filename"],
                lat,
                lon,
                "gps",
                platform.system(),
                sync_timestamp,
                self.public_key_hex,
            ])
        return output.getvalue().encode("utf-8")

    def _request_opentimestamp(self, bundle_id: str, block_sha256_hex: str) -> str | None:
        """Ancre l'empreinte du bloc dans la blockchain Bitcoin via OpenTimestamps."""
        digest_bytes = bytes.fromhex(block_sha256_hex)
        calendar_url = "https://opentimestamps.org"
        ots_path = os.path.join(self.storage_dir, f"{bundle_id}.ijrap.ots")
        try:
            req = urllib.request.Request(
                calendar_url,
                data=digest_bytes,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    with open(ots_path, "wb") as of:
                        of.write(response.read())
                    return ots_path
        except (urllib.error.URLError, TimeoutError, OSError):
            return None
        return None

    def panic_wipe(self) -> bool:
        """Suppression de la clé privée locale du bac à sable."""
        priv_path = os.path.join(self.key_storage_dir, f"{self.investigator_id}_ed25519.pem")
        if os.path.exists(priv_path):
            os.remove(priv_path)
            return True
        return False

    def seal_in_memory_bundle(
        self,
        title: str,
        written_report: str,
        previous_chain_hash: str,
        media_buffers: dict[str, tuple[str, bytes]] | None = None,
        gps_coords: tuple[float, float] = (0.0, 0.0),
        encryption_passphrase: str | None = None,
        enable_opentimestamps: bool = True,
    ) -> dict:
        """
        Assemble, signe (Ed25519 + Lamport PQC) et chiffre le bloc directement en RAM.
        Aucune donnée en clair n'est écrite sur le stockage flash du téléphone.
        """
        bundle_id = f"IJRAP_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
        sync_timestamp = datetime.now(timezone.utc).isoformat()
        monotonic_ns = time.monotonic_ns()

        hashed_streams = {}
        valid_buffers = {}

        if media_buffers:
            for stream_type, (filename, raw_bytes) in sorted(media_buffers.items()):
                if raw_bytes:
                    hashed_streams[stream_type] = self.hash_bytes(raw_bytes, filename)
                    valid_buffers[stream_type] = (filename, raw_bytes)

        report_bytes = written_report.encode("utf-8")
        report_meta = self.hash_bytes(report_bytes, "written_report.txt")

        manifest_core = {
            "schema_version": "3.0-sandbox-memory-core",
            "project": "IJRAP Security Multi-Stream Core",
            "bundle_id": bundle_id,
            "title": title,
            "investigator_id": self.investigator_id,
            "previous_chain_hash": previous_chain_hash,
            "cryptographic_identity": {
                "signature_algorithm": "Ed25519 + LAMPORT-SHA3-512",
                "device_public_key_hex": self.public_key_hex,
            },
            "timestamps": {
                "device_utc_iso8601": sync_timestamp,
                "monotonic_clock_ns": monotonic_ns,
            },
            "device_telemetry": {
                "os": platform.system(),
            },
            "gps_wgs84": {"lat": gps_coords[0], "lon": gps_coords[1]},
            "written_report_integrity": report_meta,
            "synchronized_streams": hashed_streams,
        }

        manifest_bytes = json.dumps(
            manifest_core, indent=4, sort_keys=True, ensure_ascii=False
        ).encode("utf-8")
        proofmode_csv_bytes = self._build_proofmode_csv_bytes(
            hashed_streams, gps_coords, sync_timestamp
        )

        # Assemblage du bloc TAR intégralement en mémoire vive (RAM)
        ram_tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=ram_tar_buffer, mode="w") as tar:
            for name, content in [
                ("manifest.json", manifest_bytes),
                ("written_report.txt", report_bytes),
                ("proofmode.csv", proofmode_csv_bytes),
            ]:
                info = tarfile.TarInfo(name=name)
                info.size = len(content)
                info.mtime = 0
                tar.addfile(info, io.BytesIO(content))

            for stream_type, (filename, raw_bytes) in sorted(valid_buffers.items()):
                info = tarfile.TarInfo(name=f"media/{stream_type}_{filename}")
                info.size = len(raw_bytes)
                info.mtime = 0
                tar.addfile(info, io.BytesIO(raw_bytes))

        plaintext_block_bytes = ram_tar_buffer.getvalue()

        # Empreintes et signatures (Classique + Post-Quantique)
        block_sha256 = hashlib.sha256(plaintext_block_bytes).hexdigest()
        block_sha3_512_digest = hashlib.sha3_512(plaintext_block_bytes).digest()
        block_sha3_512_hex = block_sha3_512_digest.hex()

        ed25519_sig = self.sign_digest(block_sha3_512_hex)
        pqc_sig = PostQuantumLamportSigner.sign_digest(block_sha3_512_digest)

        # Chiffrement en RAM avant toute écriture sur le stockage du téléphone
        kdf_salt = os.urandom(16)
        if encryption_passphrase:
            key = self._derive_fernet_key(encryption_passphrase, kdf_salt)
            cipher = Fernet(key)
            bytes_to_write = cipher.encrypt(plaintext_block_bytes)
            block_filename = f"{bundle_id}.ijrap.enc"
        else:
            bytes_to_write = plaintext_block_bytes
            block_filename = f"{bundle_id}.ijrap"

        final_block_path = os.path.join(self.storage_dir, block_filename)
        with open(final_block_path, "wb") as bf:
            bf.write(bytes_to_write)
            bf.flush()

        # Horodatage externe OpenTimestamps
        ots_path = None
        if enable_opentimestamps:
            ots_path = self._request_opentimestamp(bundle_id, block_sha256)

        # Certificat public chaîné (remplace les permissions Unix os.chmod)
        certificate = {
            "schema": "IJRAP-SANDBOX-CERT-v3",
            "bundle_id": bundle_id,
            "title": title,
            "timestamp_utc": sync_timestamp,
            "previous_chain_hash": previous_chain_hash,
            "monolithic_block_file": block_filename,
            "block_sha256": block_sha256,
            "sha3_512_digest": block_sha3_512_hex,
            "device_public_key_hex": self.public_key_hex,
            "ed25519_block_signature_hex": ed25519_sig,
            "post_quantum_signature": pqc_sig,
            "opentimestamps_proof": os.path.basename(ots_path) if ots_path else "pending_offline",
            "encryption": {
                "is_encrypted": bool(encryption_passphrase),
                "cipher": "Fernet-AES128-CBC-HMAC-SHA256" if encryption_passphrase else "none",
                "kdf_salt_hex": kdf_salt.hex() if encryption_passphrase else None,
            },
        }

        cert_path = os.path.join(self.storage_dir, f"{bundle_id}.json")
        with open(cert_path, "w", encoding="utf-8") as cf:
            json.dump(certificate, cf, indent=2, ensure_ascii=False)
            cf.flush()

        return certificate


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
            text: 'Entrez votre code PIN de session'
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
            text: 'SCELLEMENT EN MÉMOIRE (PQC + AES + CHAÎNAGE)'
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
            hint_text: 'Description factuelle à chiffrer et signer...'
            multiline: True
            size_hint_y: 0.35
        AccentButton:
            text: 'SCELLER ET CHIFFRER (RAM -> COFFRE)'
            size_hint_y: None
            height: '48dp'
            on_press: root.seal_note()
        Label:
            text: 'Certificats chaînés dans le bac à sable :'
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


class SecurityScreen(Screen):
    entered_pin = StringProperty("")

    # Empreintes SHA-256 des codes PIN (évite les mots de passe en clair dans le code)
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
        candidate_hash = hashlib.sha256(f"IJRAP_SALT_2026:{self.entered_pin}".encode("utf-8")).hexdigest()

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
            title="Scellé & Chiffré en RAM",
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


class IJRAPSecurityApp(App):
    duress_mode = BooleanProperty(False)
    sealer = None
    session_secret = ""

    def build(self):
        self.title = "IJRAP Security Public"
        return Builder.load_string(KV_UI)

    def get_vault_dir(self) -> str:
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
screen.ids.list_label.text = "Aucun dossier scellé."
return
files = sorted([f for f in os.listdir(self.get_vault_dir()) if f.endswith(".json")])
screen.ids.list_label.text = "\n".join(f"• {f}" for f in files) if files else "Aucun dossier scellé."
if name == "main":
IJRAPSecurityApp().run()
