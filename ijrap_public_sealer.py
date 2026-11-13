#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 ADZE Kossivi Edem (IJRAP Media / IJRAP LABS)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.

import hashlib
import json
import os
import stat
from datetime import datetime, timezone


class IJRAPForensicSealer:
    """
    IJRAP Security - Multi-Stream Forensic Sealing Engine (IJRAP Citizen Public Tier)
    Synchronizes and seals Audio, Video, Photo, and Written Text into a single proof.
    Author: ADZE Kossivi Edem (IJRAP LABS / IJRAP Media)
    License: GNU AGPLv3 (https://gnu.org)
    """

    def __init__(self, investigator_id: str):
        self.investigator_id = investigator_id

    def hash_single_file(self, file_path: str) -> dict:
        """Generates dual SHA-256 and post-quantum resistant SHA-3-256 hashes for a file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Media stream not found: {file_path}")

        sha256 = hashlib.sha256()
        sha3_256 = hashlib.sha3_256()

        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
                sha3_256.update(chunk)

        return {
            "filename": os.path.basename(file_path),
            "size_bytes": os.path.getsize(file_path),
            "sha256": sha256.hexdigest(),
            "sha3_256": sha3_256.hexdigest(),
        }

    def compute_master_seal(self, manifest_data: dict) -> str:
        """Computes a single cryptographic master seal over all synchronized streams and metadata."""
        canonical_bytes = json.dumps(manifest_data, sort_keys=True).encode("utf-8")
        h256 = hashlib.sha256(canonical_bytes).hexdigest()
        h3_256 = hashlib.sha3_256(canonical_bytes).hexdigest()
        combined = f"{h256}:{h3_256}"
        return hashlib.sha3_256(combined.encode("utf-8")).hexdigest()

    def seal_synchronized_bundle(
        self,
        bundle_id: str,
        media_streams: dict,
        gps_coords: tuple,
        written_report: str,
    ) -> str:
        """
        Binds audio, video, photo, and written text with unified GPS & UTC timestamp,
        creates a master cryptographic seal, and enforces WORM read-only lock on all files.
        """
        sync_timestamp = datetime.now(timezone.utc).isoformat()
        hashed_streams = {}

        for stream_type, path in media_streams.items():
            if path and os.path.exists(path):
                hashed_streams[stream_type] = self.hash_single_file(path)

        manifest_core = {
            "project": "IJRAP Security Multi-Stream Core",
            "bundle_id": bundle_id,
            "investigator_id": self.investigator_id,
            "synchronized_timestamp_utc": sync_timestamp,
            "gps_wgs84": {"lat": gps_coords[0], "lon": gps_coords[1]},
            "written_statement": written_report,
            "synchronized_streams": hashed_streams,
        }

        master_seal = self.compute_master_seal(manifest_core)

        seal_package = {
            "manifest": manifest_core,
            "master_bundle_seal_sha3_256": master_seal,
        }

        manifest_path = f"{bundle_id}.ijrap_bundle_seal.json"
        with open(manifest_path, "w", encoding="utf-8") as mf:
            json.dump(seal_package, mf, indent=4, ensure_ascii=False)

        # Enforce OS-level WORM (0o444 read-only) on all media files and the master manifest
        for path in media_streams.values():
            if path and os.path.exists(path):
                os.chmod(path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

        os.chmod(manifest_path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

        return manifest_path

    def verify_bundle_integrity(self, base_dir: str, manifest_path: str) -> bool:
        """Verifies that all media streams (audio, video, photo, text) remain unaltered."""
        with open(manifest_path, "r", encoding="utf-8") as mf:
            seal_package = json.load(mf)

        manifest_core = seal_package["manifest"]
        stored_master_seal = seal_package["master_bundle_seal_sha3_256"]

        # 1. Verify master manifest integrity
        if self.compute_master_seal(manifest_core) != stored_master_seal:
            return False

        # 2. Verify each individual media file against its recorded hashes
        for stream_type, info in manifest_core["synchronized_streams"].items():
            file_path = os.path.join(base_dir, info["filename"])
            if not os.path.exists(file_path):
                return False

            current_hashes = self.hash_single_file(file_path)
            if (
                current_hashes["sha256"] != info["sha256"]
                or current_hashes["sha3_256"] != info["sha3_256"]
            ):
                return False

        return True


if __name__ == "__main__":
    
    print("=== IJRAP SECURITY: MULTI-STREAM SYNCHRONIZED SEALING ===\n")

    # Simulated field capture files (Audio, Video, Photo, Text)
    sample_files = {
        "audio": "capture_audio.wav",
        "video": "capture_video.mp4",
        "photo": "capture_photo.jpg",
        "text_note": "capture_notes.txt",
    }

    for key, fname in sample_files.items():
        if os.path.exists(fname):
            os.chmod(fname, stat.S_IWUSR | stat.S_IRUSR)
        with open(fname, "wb") as f:
            f.write(f"Simulated binary/text stream data for {key}".encode("utf-8"))

    bundle_name = "EVIDENCE_LOME_2026_001"
    if os.path.exists(f"{bundle_name}.ijrap_bundle_seal.json"):
        os.chmod(f"{bundle_name}.ijrap_bundle_seal.json", stat.S_IWUSR | stat.S_IRUSR)

    sealer = IJRAPForensicSealer(investigator_id="IJRAP-JOURNALIST-001")
    manifest_file = sealer.seal_synchronized_bundle(
        bundle_id=bundle_name,
        media_streams=sample_files,
        gps_coords=(6.1375, 1.2123),
        written_report="Synchronized field documentation: Audio, video, photo, and written testimony captured simultaneously.",
    )
    print(f"[OK] All streams synchronized and sealed (WORM 0o444): {manifest_file}")

    is_valid = sealer.verify_bundle_integrity(".", manifest_file)
    print(
        f"[VERIFICATION] Multi-stream proof status: {'VALID (ALL STREAMS UNALTERED)' if is_valid else 'COMPROMISED'}"
    )
