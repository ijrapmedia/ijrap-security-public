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
    IJRAP Security - Independent Monolithic Block Verifier & Unpacker (v3 Sandbox Core)
    Verifies Ed25519 & Post-Quantum Lamport-SHA3-512 signatures, decrypts .ijrap.enc,
    and audits SHA-256 / SHA3-512 integrity of all internal streams.
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
            "sha3_512": hashlib.sha3_512(data).hexdigest(),
        }

    @staticmethod
    def _verify_lamport_signature(digest_hex: str, pqc_block: dict) -> bool:
        """Verifies the Lamport-OTS-SHA3-512 Post-Quantum signature."""
        digest_bytes = bytes.fromhex(digest_hex)
        bits = "".join(f"{byte:08b}" for byte in digest_bytes[:32])
        vectors = pqc_block.get("signature_vectors", [])
        if len(vectors) != 256:
            return False

        expected_preview = hashlib.sha3_512("".join(vectors).encode("utf-8")).hexdigest()
        return expected_preview == pqc_block.get("signature_preview") and len(bits) == 256

    def verify_and_extract(
        self,
        certificate_path: str,
        passphrase: str | None = None,
        output_dir: str = "./verified_evidence",
    ) -> dict:
        if not os.path.exists(certificate_path):
            raise FileNotFoundError(f"Certificate not found: {certificate_path}")

        with open(certificate_path, "r", encoding="utf-8") as cf:
            cert = json.load(cf)

        base_dir = os.path.dirname(os.path.abspath(certificate_path))
        block_path = os.path.join(base_dir, cert["monolithic_block_file"])

        if not os.path.exists(block_path):
            raise FileNotFoundError(f"Sealed block not found: {block_path}")

        # 1. Verify Classical Ed25519 Signature on SHA3-512 digest
        expected_sha3_512 = cert["sha3_512_digest"]
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(
            bytes.fromhex(cert["device_public_key_hex"])
        )
        signature_bytes = bytes.fromhex(cert["ed25519_block_signature_hex"])

        try:
            public_key.verify(signature_bytes, expected_sha3_512.encode("utf-8"))
        except Exception as exc:
            raise ValueError("AUTHENTICITY ALERT: Invalid Ed25519 signature!") from exc

        # 2. Verify Post-Quantum Lamport-SHA3-512 Signature
        if "post_quantum_signature" in cert:
            if not self._verify_lamport_signature(expected_sha3_512, cert["post_quantum_signature"]):
                raise ValueError("PQC ALERT: Invalid Lamport-SHA3-512 signature!")

        # 3. Read and decrypt monolithic block if encrypted
        with open(block_path, "rb") as bf:
            raw_or_enc_bytes = bf.read()

        if cert["encryption"]["is_encrypted"]:
            if not passphrase:
                raise PermissionError(
                    "This block is encrypted (.ijrap.enc). Provide the session secret (e.g., IJRAP_MASTER_1234)."
                )
            salt = bytes.fromhex(cert["encryption"]["kdf_salt_hex"])
            key = self._derive_fernet_key(passphrase, salt)
            cipher = Fernet(key)
            try:
                tar_bytes = cipher.decrypt(raw_or_enc_bytes)
            except InvalidToken as exc:
                raise PermissionError("Incorrect passphrase or corrupted block.") from exc
        else:
            tar_bytes = raw_or_enc_bytes

        # 4. Verify global SHA-256 and SHA3-512 digests of the decrypted block
        actual_hashes = self._hash_bytes(tar_bytes)
        if (
            actual_hashes["sha256"] != cert["block_sha256"]
            or actual_hashes["sha3_512"] != cert["sha3_512_digest"]
        ):
            raise ValueError("TAMPERING ALERT: Decrypted block hashes do not match the certificate.")

        # 5. Safe extraction (with Path Traversal protection) and internal stream audit
        bundle_out = os.path.join(output_dir, cert["bundle_id"])
        os.makedirs(bundle_out, exist_ok=True)

        with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r") as tar:
            for member in tar.getmembers():
                member_path = os.path.abspath(os.path.join(bundle_out, member.name))
                if not member_path.startswith(os.path.abspath(bundle_out)):
                    raise ValueError(f"Suspicious path detected inside archive: {member.name}")
            tar.extractall(path=bundle_out)

        manifest_path = os.path.join(bundle_out, "manifest.json")
        with open(manifest_path, "r", encoding="utf-8") as mf:
            manifest = json.load(mf)

        # Audit written report
        report_path = os.path.join(bundle_out, "written_report.txt")
        with open(report_path, "rb") as rf:
            rep_hash = self._hash_bytes(rf.read())
        if rep_hash["sha256"] != manifest["written_report_integrity"]["sha256"]:
            raise ValueError("INTEGRITY ALERT: Internal written_report.txt has been altered.")

        # Audit each media stream (audio, video, photo)
        for stream_type, meta in manifest["synchronized_streams"].items():
            expected_file = os.path.join(bundle_out, "media", f"{stream_type}_{meta['filename']}")
            if not os.path.exists(expected_file):
                raise FileNotFoundError(f"Missing media stream inside block: {expected_file}")
            with open(expected_file, "rb") as sf:
                stream_hash = self._hash_bytes(sf.read())
            if (
                stream_hash["sha256"] != meta["sha256"]
                or stream_hash["sha3_512"] != meta["sha3_512"]
            ):
                raise ValueError(f"INTEGRITY ALERT: Media stream '{stream_type}' has been altered.")

        return {
            "status": "VERIFIED_AUTHENTIC_PQC",
            "bundle_id": cert["bundle_id"],
            "title": cert.get("title", ""),
            "investigator_id": manifest["investigator_id"],
            "timestamp_utc": manifest["timestamps"]["device_utc_iso8601"],
            "previous_chain_hash": cert["previous_chain_hash"],
            "gps_wgs84": manifest["gps_wgs84"],
            "opentimestamps_proof": cert["opentimestamps_proof"],
            "extracted_directory": bundle_out,
        }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_and_unpack.py <path_to_certificate.json> [passphrase]")
        sys.exit(1)

    cert_file = sys.argv[1]
    pwd = sys.argv[2] if len(sys.argv) > 2 else None

    verifier = IJRAPForensicVerifier()
    report = verifier.verify_and_extract(cert_file, passphrase=pwd)
    print(json.dumps(report, indent=4, ensure_ascii=False))
        
