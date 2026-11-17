#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 ADZE Kossivi Edem (IJRAP Media / IJRAP LABS)

import base64
import hashlib
import io
import json
import os
import sys
import tarfile

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class IJRAPForensicVerifier:
    """
    IJRAP Security - Independent Monolithic Block Verifier & Unpacker
    Vérifie la signature Ed25519, déchiffre le conteneur .ijrap.enc (Tella-style)
    et contrôle l'intégrité SHA-256 / SHA3-256 de chaque preuve interne.
    """

    @staticmethod
    def _derive_fernet_key(passphrase: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        return base64.urlsafe_b64encode(kdf.derive(passphrase.encode("utf-8")))

    @staticmethod
    def _hash_bytes(data: bytes) -> dict:
        return {
            "size_bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "sha3_256": hashlib.sha3_256(data).hexdigest(),
        }

    def verify_and_extract(
        self,
        certificate_path: str,
        passphrase: str | None = None,
        output_dir: str = "./verified_evidence",
    ) -> dict:
        if not os.path.exists(certificate_path):
            raise FileNotFoundError(f"Certificat introuvable : {certificate_path}")

        with open(certificate_path, "r", encoding="utf-8") as cf:
            cert = json.load(cf)

        base_dir = os.path.dirname(os.path.abspath(certificate_path))
        block_path = os.path.join(base_dir, cert["monolithic_block_file"])

        if not os.path.exists(block_path):
            raise FileNotFoundError(f"Bloc scellé introuvable : {block_path}")

        # 1. Vérification mathématique de la signature publique Ed25519 sur le certificat
        combined_digest = f"{cert['block_sha256']}:{cert['block_sha3_256']}"
        expected_master_seal = hashlib.sha3_256(combined_digest.encode("utf-8")).hexdigest()

        if expected_master_seal != cert["monolithic_master_seal_sha3_256"]:
            raise ValueError("ALERTE INTÉGRITÉ : Le sceau maître du certificat a été altéré.")

        public_key = ed25519.Ed25519PublicKey.from_public_bytes(
            bytes.fromhex(cert["device_public_key_hex"])
        )
        signature_bytes = bytes.fromhex(cert["ed25519_block_signature_hex"])

        try:
            public_key.verify(signature_bytes, expected_master_seal.encode("utf-8"))
        except Exception as exc:
            raise ValueError("ALERTE AUTHENTICITÉ : Signature Ed25519 invalide !") from exc

        # 2. Lecture et déchiffrement éventuel du bloc monolithique
        with open(block_path, "rb") as bf:
            raw_or_enc_bytes = bf.read()

        if cert["encryption"]["is_encrypted"]:
            if not passphrase:
                raise PermissionError(
                    "Ce bloc est chiffré (.ijrap.enc). Fournissez le mot de passe terrain."
                )
            salt = bytes.fromhex(cert["encryption"]["kdf_salt_hex"])
            key = self._derive_fernet_key(passphrase, salt)
            cipher = Fernet(key)
            try:
                tar_bytes = cipher.decrypt(raw_or_enc_bytes)
            except InvalidToken as exc:
                raise PermissionError("Mot de passe incorrect ou bloc corrompu.") from exc
        else:
            tar_bytes = raw_or_enc_bytes

        # 3. Contrôle de l'empreinte globale du bloc déchiffré
        actual_hashes = self._hash_bytes(tar_bytes)
        if (
            actual_hashes["sha256"] != cert["block_sha256"]
            or actual_hashes["sha3_256"] != cert["block_sha3_256"]
        ):
            raise ValueError("ALERTE FALSIFICATION : Le contenu du bloc ne correspond pas au certificat.")

        # 4. Extraction sécurisée et audit interne de chaque preuve (audio, vidéo, photo, écrit)
        bundle_out = os.path.join(output_dir, cert["bundle_id"])
        os.makedirs(bundle_out, exist_ok=True)

        with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r") as tar:
            # Prévention contre les attaques Path Traversal lors de l'extraction
            for member in tar.getmembers():
                member_path = os.path.abspath(os.path.join(bundle_out, member.name))
                if not member_path.startswith(os.path.abspath(bundle_out)):
                    raise ValueError(f"Chemin suspect détecté dans l'archive : {member.name}")
            tar.extractall(path=bundle_out)

        manifest_path = os.path.join(bundle_out, "manifest.json")
        with open(manifest_path, "r", encoding="utf-8") as mf:
            manifest = json.load(mf)

        # Audit du rapport écrit
        report_path = os.path.join(bundle_out, "written_report.txt")
        with open(report_path, "rb") as rf:
            rep_hash = self._hash_bytes(rf.read())
        if rep_hash["sha256"] != manifest["written_report_integrity"]["sha256"]:
            raise ValueError("ALERTE : Le rapport écrit interne a été modifié.")

        # Audit de chaque flux média (audio, vidéo, photo)
        for stream_type, meta in manifest["synchronized_streams"].items():
            expected_file = os.path.join(bundle_out, "media", f"{stream_type}_{meta['filename']}")
            if not os.path.exists(expected_file):
                raise FileNotFoundError(f"Flux média manquant dans le bloc : {expected_file}")
            with open(expected_file, "rb") as sf:
                stream_hash = self._hash_bytes(sf.read())
            if (
                stream_hash["sha256"] != meta["sha256"]
                or stream_hash["sha3_256"] != meta["sha3_256"]
            ):
                raise ValueError(f"ALERTE : Le flux '{stream_type}' a été altéré.")

        return {
            "status": "VERIFIED_AUTHENTIC",
            "bundle_id": cert["bundle_id"],
            "investigator_id": manifest["investigator_id"],
            "timestamp_utc": manifest["timestamps"]["device_utc_iso8601"],
            "gps_wgs84": manifest["gps_wgs84"],
            "opentimestamps_proof": cert["opentimestamps_proof"],
            "extracted_directory": bundle_out,
        }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_and_unpack.py <chemin_vers_certificat.json> [mot_de_passe]")
        sys.exit(1)

    cert_file = sys.argv[1]
    pwd = sys.argv[2] if len(sys.argv) > 2 else None

    verifier = IJRAPForensicVerifier()
    report = verifier.verify_and_extract(cert_file, passphrase=pwd)
    print(json.dumps(report, indent=4, ensure_ascii=False))
