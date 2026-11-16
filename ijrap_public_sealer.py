#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 ADZE Kossivi Edem (IJRAP Media / IJRAP LABS)

import hashlib
import json
import os
import platform
import stat
import time
import uuid
from datetime import datetime, timezone


class IJRAPForensicSealer:
    """
    IJRAP Security - Multi-Stream Forensic Sealing Engine (IJRAP Citizen Public Tier)
    """

    def __init__(self, investigator_id: str, storage_dir: str = "."):
        self.investigator_id = investigator_id
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    def hash_single_file(self, file_path: str) -> dict:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Media stream not found: {file_path}")

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

    def compute_master_seal(self, manifest_data: dict) -> str:
        canonical_bytes = json.dumps(manifest_data, sort_keys=True, separators=(",", ":")).encode("utf-8")
        h256 = hashlib.sha256(canonical_bytes).hexdigest()
        h3_256 = hashlib.sha3_256(canonical_bytes).hexdigest()
        combined = f"{h256}:{h3_256}"
        return hashlib.sha3_256(combined.encode("utf-8")).hexdigest()

    def _atomic_write_json(self, target_path: str, data: dict) -> None:
        temp_path = f"{target_path}.{uuid.uuid4().hex}.tmp"
        with open(temp_path, "w", encoding="utf-8") as tf:
            json.dump(data, tf, indent=4, ensure_ascii=False)
            tf.flush()
            os.fsync(tf.fileno())
        os.replace(temp_path, target_path)

    def _try_lock_readonly(self, file_path: str) -> bool:
        try:
            os.chmod(file_path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
            return True
        except OSError:
            return False

    def seal_synchronized_bundle(
        self,
        bundle_id: str,
        media_streams: dict,
        gps_coords: tuple,
        written_report: str,
        battery_level: int = -1,
    ) -> str:
        sync_timestamp = datetime.now(timezone.utc).isoformat()
        monotonic_ns = time.monotonic_ns()
        hashed_streams = {}
        worm_status = {}

        for stream_type, path in media_streams.items():
            if path and os.path.exists(path):
                hashed_streams[stream_type] = self.hash_single_file(path)

        manifest_core = {
            "schema_version": "1.0-public",
            "project": "IJRAP Security Multi-Stream Core",
            "evidence_uuid": str(uuid.uuid4()),
            "bundle_id": bundle_id,
            "investigator_id": self.investigator_id,
            "timestamps": {
                "device_utc_iso8601": sync_timestamp,
                "monotonic_clock_ns": monotonic_ns,
            },
            "device_telemetry": {
                "os": platform.system(),
                "battery_percent": battery_level,
            },
            "gps_wgs84": {"lat": gps_coords[0], "lon": gps_coords[1]},
            "written_statement": written_report,
            "synchronized_streams": hashed_streams,
        }

        master_seal = self.compute_master_seal(manifest_core)

        for stream_type, path in media_streams.items():
            if path and os.path.exists(path):
                worm_status[stream_type] = self._try_lock_readonly(path)

        seal_package = {
            "manifest": manifest_core,
            "master_bundle_seal_sha3_256": master_seal,
            "os_worm_applied": worm_status,
        }

        manifest_path = os.path.join(self.storage_dir, f"{bundle_id}.ijrap_bundle_seal.json")
        self._atomic_write_json(manifest_path, seal_package)
        self._try_lock_readonly(manifest_path)

        return manifest_path
