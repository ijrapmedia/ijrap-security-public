# IJRAP Security: Multi-Stream Forensic Truth-Preservation Core

**Founding Author & Sovereign Copyright Holder:** ADZE Kossivi Edem (IJRAP LABS / IJRAP Media)  
**Academic Reference:** Zenodo: https://zenodo.org/record/23139273 | **ORCID:** https://orcid.org/0009-0009-0018-6734  
**Status:** Open-Source Public Reference Implementation (GNU AGPLv3 — Schema `3.0-sandbox-memory-core`)

---

## Mission & Overview

The core mission of **IJRAP Security** is to secure empirical field data at its source using cryptographic fingerprints. Designed to counter deepfakes, metadata tampering, and hostile field conditions (zero-internet, risk of seizure), it transforms standard mobile and desktop devices into tamper-proof evidence vaults by uniting investigative reporting with forensic science.

Our strategic focus is on independent journalists, citizen reporters, whistleblowers, and NGOs who need mathematically verifiable chains of custody. Engineered specifically around **in-memory (RAM) processing**, IJRAP Security respects strict mobile application sandboxing (Android / iOS) and avoids leaving plaintext artifacts on device flash storage.

## Core Technical Capabilities

- **In-Memory (RAM) Monolithic Sealing (`.ijrap` / `.ijrap.enc`):** Assembles live audio, video, photo buffers, written testimony, and `proofmode.csv` metadata strictly in volatile memory (`io.BytesIO`) into a single indivisible container (`schema_version: 3.0-sandbox-memory-core`) before encryption and disk write.
- **Hybrid Classical & Post-Quantum Signatures:** Combines classical **Ed25519** device signatures (with password-encrypted local `.pem` keys) alongside pure-Python **Post-Quantum Lamport-SHA3-512** hash-based signatures.
- **Cryptographic Hash Chaining (`SHA3-512`):** Links sequential evidence certificates (`<bundle_id>.json`) via `previous_chain_hash`, guaranteeing tamper-evident immutability inside mobile sandboxes without relying on fragile Unix file permissions.
- **ProofMode Interoperability:** Generates Guardian Project-compatible `proofmode.csv` telemetry records inside every sealed evidence block.
- **Anti-Seizure Encryption & Panic Wipe (Tella-Inspired):** Encrypts the entire `.ijrap` container in RAM prior to storage (`.ijrap.enc` using PBKDF2-HMAC-SHA256 + Fernet) so no unencrypted media ever touches flash memory, complemented by an emergency `panic_wipe()` function to destroy the local signing key.
- **Decentralized Timestamping (OpenTimestamps):** Anchors the 32-byte SHA-256 digest of the monolithic block onto the Bitcoin blockchain via OpenTimestamps (`.ijrap.ots`) when online, while remaining 100% non-blocking in offline field environments (`pending_offline`).

## Strict "Zero-Gallery" Policy & Volatile Memory (RAM) Capture

Unlike consumer-grade media verification tools that allow users to import pre-existing files from a device's local gallery, **IJRAP Security enforces a strict Zero-Gallery, Live-Capture-Only architecture**:

* **Prevention of Pre-Capture Tampering:** Access to the device's public gallery and external file picker is completely blocked at the application level. All audiovisual streams (photo, video, audio) and written field notes must be captured live through hardware sensors at the exact moment of investigation.
* **In-Memory Forensic Sealing (RAM-Only):** Captured media buffers, consent metadata, and cryptographic signatures (Ed25519, Lamport PQC, C2PA Content Credentials) are assembled, hashed, and encrypted strictly in volatile memory (RAM) via `ijrap_seal.py` and `c2pa_bridge.py`.
* **Zero Plaintext Disk Footprint:** Unsealed or unencrypted media is never written to the device's flash storage, eliminating the risk of file substitution, synthetic media injection (deepfakes), or unauthorized local tampering prior to sealing.
  
## Prerequisites

- **Python 3.10 or higher** must be installed on your machine (verify with `python --version`).
- **Dependencies:** `kivy==2.3.0` and `cryptography>=42.0.0` (listed in `requirements.txt`).

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ijrapmedia/ijrap-security-public.git
   cd ijrap-security-public
   ```

2. **Install the required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### 1. Sealing Evidence Programmatically (`ijrap_seal.py`)

```python
from ijrap_seal import IJRAPForensicSealer

sealer = IJRAPForensicSealer(
    investigator_id="IJRAP-FIELD-01",
    vault_dir="./vault",
    key_passphrase="YourStrongKeyPassphrase",
)

cert = sealer.seal_in_memory_bundle(
    title="Field Observation 01",
    written_report="Factual statement recorded on site.",
    previous_chain_hash="0" * 128,
    media_buffers={
        "photo": ("evidence.jpg", b"...raw_image_bytes..."),
    },
    gps_coords=(6.1319, 1.2228),
    encryption_passphrase="YourStrongVaultPassphrase",
    enable_opentimestamps=True,
)

print("Bundle ID:", cert["bundle_id"])
print("Sealed Block:", cert["monolithic_block_file"])
print("SHA3-512 Digest:", cert["sha3_512_digest"])
```

### 2. Mobile App Prototype (`main.py`)

This repository includes a lightweight **Kivy mobile application** (`main.py`) featuring:
- **Duress & Decoy PIN Vault:** Operational protection against forced device unlocking (`1234` standard vault / `9999` decoy empty view).
- **One-Tap Panic Wipe:** Immediate deletion of the local encrypted Ed25519 private key from the app sandbox.
- **Automated APK Pipeline:** Configured via `buildozer.spec` and GitHub Actions (`.github/workflows/main.yml`).

To run the mobile UI locally on a desktop for testing:
```bash
python main.py
```

### 3. Independent Verification & Unpacking (`verify_and_unpack.py`)

Audit any public certificate (`<bundle_id>.json`), verify both **Ed25519** and **Lamport-SHA3-512** signatures, decrypt `.ijrap.enc` containers, and extract verified files:
```bash
python verify_and_unpack.py ./vault/IJRAP_20261117T100000Z_ab12cd34.json IJRAP_MASTER_1234
```

## Roadmap & Open Collaboration

We welcome security engineers, mobile developers, and civic-tech contributors to open **Issues** or **Pull Requests** on the following milestones:
- **Hardware-Backed Attestation:** Bridging `proofmode.csv` metadata and Ed25519 device keys with hardware-backed Android Keystore / StrongBox and iOS Secure Enclave attestation.
- **Native Hardware Bridge:** Integrating native Android/iOS camera, microphone, and GPS sensor streams directly into memory buffers (`media_buffers`).
- **NIST Post-Quantum Standardization:** Integrating NIST-standardized PQ signature schemes (ML-DSA / SLH-DSA) alongside Ed25519 and Lamport-SHA3-512.

## License & Contact

- **License:** Released under the **GNU AGPLv3** open-source license (an enterprise tier is also available for institutional clients).
- **Contact:** `ijraplabs@proton.me` | `imoadze1@gmail.com`
