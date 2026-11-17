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
import stat
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


class IJRAPForensicSealer:
    """
    IJRAP Security - Monolithic Multi-Stream Forensic Sealing Engine (IJRAP Citizen Public Tier)
    Scelle audio, vidéo, photo, rapport écrit et métadonnées ProofMode en un bloc unique indissociable,
    suivi de la signature Ed25519, de l'horodatage OpenTimestamps et du chiffrement global (Tella).
    """

    def __init__(
        self,
        investigator_id: str,
        storage_dir: str = ".",
        key_storage_dir: str | None = None,
    ):
        self.investigator_id = investigator_id
        self.storage_dir = storage_dir
        self.key_storage_dir = key_storage_dir or os.path.join(storage_dir, ".ijrap_keystore")
        os.makedirs(self.storage_dir, exist_ok=True)
        os.makedirs(self.key_storage_dir, exist_ok=True)

        self._private_key, self.public_key_hex = self._load_or_create_device_keys()

    def _load_or_create_device_keys(self) -> tuple[ed25519.Ed25519PrivateKey, str]:
        """Génère ou charge la paire de clés Ed25519 locale de l'appareil."""
        priv_path = os.path.join(self.key_storage_dir, f"{self.investigator_id}_ed25519.pem")

        if os.path.exists(priv_path):
            with open(priv_path, "rb") as kf:
                private_key = serialization.load_pem_private_key(kf.read(), password=None)
        else:
            private_key = ed25519.Ed25519PrivateKey.generate()
            pem_bytes = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
            with open(priv_path, "wb") as kf:
                kf.write(pem_bytes)
            try:
                os.chmod(priv_path, stat.S_IRUSR | stat.S_IWUSR)
            except OSError:
                pass

        pub_bytes = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return private_key, pub_bytes.hex()

    def hash_single_file(self, file_path: str) -> dict:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        sha256 = hashlib.sha256()
        sha3_256 = hashlib.sha3_256()

        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                sha256.update(chunk)
                sha3_256.update(chunk)

        return {
            "filename": os.path.basename(file_path),
            "size_bytes": os.path.getsize(file_path),
            "sha256": sha256.hexdigest(),
            "sha3_256": sha3_256.hexdigest(),
        }

    def sign_digest(self, hex_digest: str) -> str:
        """Signe une empreinte avec la clé privée Ed25519 de l'appareil."""
        return self._private_key.sign(hex_digest.encode("utf-8")).hex()

    def _derive_fernet_key(self, passphrase: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        return base64.urlsafe_b64encode(kdf.derive(passphrase.encode("utf-8")))

    def _secure_wipe_file(self, file_path: str) -> None:
        """Écrase un fichier avec des octets aléatoires avant suppression physique."""
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            with open(file_path, "wb") as wf:
                wf.write(os.urandom(size))
                wf.flush()
                os.fsync(wf.fileno())
            os.remove(file_path)

    def _encrypt_monolithic_block(self, block_path: str, passphrase: str, salt: bytes) -> str:
        """Chiffre l'intégralité du bloc scellé (médias + écrit + métadonnées) et détruit le clair."""
        key = self._derive_fernet_key(passphrase, salt)
        cipher = Fernet(key)

        with open(block_path, "rb") as f:
            encrypted_data = cipher.encrypt(f.read())

        enc_path = f"{block_path}.enc"
        with open(enc_path, "wb") as ef:
            ef.write(encrypted_data)
            ef.flush()
            os.fsync(ef.fileno())

        self._secure_wipe_file(block_path)
        return enc_path

    def _build_proofmode_csv_bytes(
        self,
        hashed_streams: dict,
        gps_coords: tuple,
        sync_timestamp: str,
    ) -> bytes:
        """Génère le contenu CSV ProofMode en mémoire pour l'inclure dans le bloc."""
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

        lat = gps_coords[0]
        lon = gps_coords[1]

        for stream_type, meta in sorted(hashed_streams.items()):
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
        """Ancre l'empreinte unique du bloc entier dans la blockchain Bitcoin via OpenTimestamps."""
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
                    self._try_lock_readonly(ots_path)
                    return ots_path
        except (urllib.error.URLError, TimeoutError, OSError):
            return None
        return None

    def _try_lock_readonly(self, file_path: str) -> bool:
        try:
            os.chmod(file_path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
            return True
        except OSError:
            return False

    def panic_wipe(self) -> bool:
        """Effacement d'urgence de la clé privée locale en cas de saisie sur le terrain."""
        priv_path = os.path.join(self.key_storage_dir, f"{self.investigator_id}_ed25519.pem")
        if os.path.exists(priv_path):
            self._secure_wipe_file(priv_path)
            return True
        return False

    def seal_synchronized_bundle(
        self,
        bundle_id: str,
        media_streams: dict,
        gps_coords: tuple,
        written_report: str,
        battery_level: int = -1,
        encryption_passphrase: str | None = None,
        enable_opentimestamps: bool = True,
    ) -> dict:
        """
        Scelle les flux (audio, vidéo, photo), le rapport écrit et les preuves ProofMode
        dans un bloc unique indissociable (.ijrap), puis applique signature, horodatage et chiffrement.
        """
        sync_timestamp = datetime.now(timezone.utc).isoformat()
        monotonic_ns = time.monotonic_ns()
        hashed_streams = {}
        valid_files = {}

        # 1. Empreintes individuelles des flux médias (audio, vidéo, photo)
        for stream_type, path in sorted(media_streams.items()):
            if path and os.path.exists(path):
                hashed_streams[stream_type] = self.hash_single_file(path)
                valid_files[stream_type] = path

        # 2. Empreinte du rapport écrit de l'enquête
        report_bytes = written_report.encode("utf-8")
        report_meta = {
            "filename": "written_report.txt",
            "size_bytes": len(report_bytes),
            "sha256": hashlib.sha256(report_bytes).hexdigest(),
            "sha3_256": hashlib.sha3_256(report_bytes).hexdigest(),
        }

        # 3. Manifeste interne complet (qui sera enfermé dans le bloc)
        manifest_core = {
            "schema_version": "2.0-monolithic-block",
            "project": "IJRAP Security Multi-Stream Core",
            "evidence_uuid": str(uuid.uuid4()),
            "bundle_id": bundle_id,
            "investigator_id": self.investigator_id,
            "cryptographic_identity": {
                "signature_algorithm": "Ed25519",
                "device_public_key_hex": self.public_key_hex,
            },
            "timestamps": {
                "device_utc_iso8601": sync_timestamp,
                "monotonic_clock_ns": monotonic_ns,
            },
            "device_telemetry": {
                "os": platform.system(),
                "battery_percent": battery_level,
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

        # 4. Création du BLOC INDISSOCIABLE (.ijrap) regroupant médias + écrit + métadonnées
        raw_block_path = os.path.join(self.storage_dir, f"{bundle_id}.ijrap")
        temp_block_path = f"{raw_block_path}.{uuid.uuid4().hex}.tmp"

        with tarfile.open(temp_block_path, "w") as tar:
            # Ajout du manifeste JSON interne
            m_info = tarfile.TarInfo(name="manifest.json")
            m_info.size = len(manifest_bytes)
            m_info.mtime = 0
            tar.addfile(m_info, io.BytesIO(manifest_bytes))

            # Ajout du rapport écrit
            r_info = tarfile.TarInfo(name="written_report.txt")
            r_info.size = len(report_bytes)
            r_info.mtime = 0
            tar.addfile(r_info, io.BytesIO(report_bytes))

            # Ajout du fichier ProofMode CSV
            p_info = tarfile.TarInfo(name="proofmode.csv")
            p_info.size = len(proofmode_csv_bytes)
            p_info.mtime = 0
            tar.addfile(p_info, io.BytesIO(proofmode_csv_bytes))

            # Ajout de tous les flux médias (audio, vidéo, photo) dans le même bloc
            for stream_type, path in sorted(valid_files.items()):
                arcname = f"media/{stream_type}_{os.path.basename(path)}"
                tar.add(path, arcname=arcname)

        os.replace(temp_block_path, raw_block_path)

        # 5. Hachage FINAL et SIGNATURE sur le bloc indissociable entier
        block_hashes = self.hash_single_file(raw_block_path)
        combined_block_digest = f"{block_hashes['sha256']}:{block_hashes['sha3_256']}"
        monolithic_master_seal = hashlib.sha3_256(
            combined_block_digest.encode("utf-8")
        ).hexdigest()
        block_signature = self.sign_digest(monolithic_master_seal)

        # 6. Horodatage externe OpenTimestamps sur l'empreinte du bloc entier
        ots_path = None
        if enable_opentimestamps:
            ots_path = self._request_opentimestamp(bundle_id, block_hashes["sha256"])

        # 7. Chiffrement du BLOC ENTIER (approche Tella) et nettoyage des sources en clair
        kdf_salt = os.urandom(16)
        if encryption_passphrase:
            final_block_path = self._encrypt_monolithic_block(
                raw_block_path, encryption_passphrase, kdf_salt
            )
            # Suppression sécurisée des fichiers originaux non protégés sur l'appareil
            for path in valid_files.values():
                self._secure_wipe_file(path)
        else:
            final_block_path = raw_block_path

        self._try_lock_readonly(final_block_path)

        # 8. Certificat public externe (permet de vérifier le bloc sans le déchiffrer)
        certificate = {
            "bundle_id": bundle_id,
            "monolithic_block_file": os.path.basename(final_block_path),
            "block_size_bytes_plaintext": block_hashes["size_bytes"],
            "block_sha256": block_hashes["sha256"],
            "block_sha3_256": block_hashes["sha3_256"],
            "monolithic_master_seal_sha3_256": monolithic_master_seal,
            "device_public_key_hex": self.public_key_hex,
            "ed25519_block_signature_hex": block_signature,
            "opentimestamps_proof": os.path.basename(ots_path) if ots_path else "pending_offline",
            "encryption": {
                "is_encrypted": bool(encryption_passphrase),
                "cipher": "Fernet-AES128-CBC-HMAC-SHA256" if encryption_passphrase else "none",
                "kdf_salt_hex": kdf_salt.hex() if encryption_passphrase else None,
            },
        }

        cert_path = os.path.join(self.storage_dir, f"{bundle_id}.ijrap_certificate.json")
        temp_cert = f"{cert_path}.{uuid.uuid4().hex}.tmp"
        with open(temp_cert, "w", encoding="utf-8") as cf:
            json.dump(certificate, cf, indent=4, ensure_ascii=False)
            cf.flush()
            os.fsync(cf.fileno())
        os.replace(temp_cert, cert_path)
        self._try_lock_readonly(cert_path)

        return {
            "sealed_block_path": final_block_path,
            "public_certificate_path": cert_path,
            "opentimestamps_path": ots_path,
        }
        
