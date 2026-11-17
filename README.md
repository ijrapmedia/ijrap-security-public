# IJRAP Security: Multi-Stream Forensic Truth-Preservation Core

**Founding Author & Sovereign Copyright Holder:** ADZE Kossivi Edem (IJRAP LABS / IJRAP Media)  
**Academic Reference:** Zenodo: https://zenodo.org/record/23139273 | **ORCID:** https://orcid.org/0009-0009-0018-6734  
**Status:** Open-Source Public Reference Implementation (GNU AGPLv3 — Schema `2.0-monolithic-block`)

---

## Mission & Overview

The core mission of **IJRAP Security** is to secure empirical field data at its source using cryptographic fingerprints. Designed to counter deepfakes, metadata tampering, and hostile field conditions (zero-internet, risk of seizure), it transforms standard devices into tamper-proof evidence vaults by uniting investigative reporting with forensic science.

Our strategic focus is on independent journalists, citizen reporters, whistleblowers, and NGOs who need mathematically verifiable chains of custody. Furthermore, IJRAP Labs ensures privacy by automating data minimization in strict compliance with GDPR regulations and collecting field data offline within encrypted structures.

## Core Technical Capabilities

- **Monolithic 4-Pillar Block Sealing (`.ijrap`):** Encapsulates live audio, video, photo, written testimony, and `proofmode.csv` metadata into a single deterministic, indivisible container (`schema_version: 2.0-monolithic-block`) prior to final hashing and encryption.
- **Hybrid Cryptographic Hashing:** Uses classical SHA-256 alongside quantum-resistant SHA-3-256 (Keccak-256) hashing on both individual streams and the sealed monolithic block.
- **Asymmetric Device Signatures (Ed25519):** Automatically generates a local Ed25519 keypair to sign the monolithic master seal and embeds the public key in the external `.ijrap_certificate.json` for independent verification without decrypting sensitive media.
- **ProofMode Interoperability:** Generates Guardian Project-compatible `proofmode.csv` telemetry records inside every sealed evidence block.
- **Anti-Seizure Encryption & Panic Wipe (Tella-Inspired):** Encrypts the entire `.ijrap` container at rest (`.ijrap.enc` using PBKDF2-HMAC-SHA256 + Fernet) and securely overwrites plaintext source files (`os.urandom` + `os.fsync`), complemented by an emergency `panic_wipe()` function for the local signing key.
- **Decentralized Timestamping (OpenTimestamps):** Anchors the 32-byte SHA-256 digest of the monolithic block onto the Bitcoin blockchain via OpenTimestamps (`.ijrap.ots`) when online, while remaining 100% non-blocking in offline field environments.
- **WORM Immutability:** Locks sealed containers, certificates, and timestamp proofs in read-only mode (`0o444`) immediately upon generation.

## Prerequisites

- **Python 3.10 or higher** must be installed on your machine (verify with `python --version`).
- **Cryptographic dependency:** Requires the `cryptography` library for Ed25519 signatures and authenticated encryption.

## Installation

1. **Clone the repository** (or download and extract the ZIP archive):
   ```bash
   git clone https://github.com/ijrapmedia/ijrap-security-public.git
   cd ijrap-security-public
   ```

2. **Install the required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Import and run the monolithic forensic sealer in your Python workflow:

```python
from ijrap_public_sealer import IJRAPForensicSealer

sealer = IJRAPForensicSealer(investigator_id="IJRAP-FIELD-01", storage_dir="./vault")

result = sealer.seal_synchronized_bundle(
    bundle_id="CASE-2026-001",
    media_streams={
        "audio": "witness_audio.wav",
        "video": "scene_video.mp4",
        "photo": "document_photo.jpg",
    },
    gps_coords=(6.1319, 1.2228),
    written_report="Field observation statement recorded on site.",
    battery_level=84,
    encryption_passphrase="YourStrongFieldPassphrase",
    enable_opentimestamps=True,
)

print("Sealed Block:", result["sealed_block_path"])
print("Public Certificate:", result["public_certificate_path"])
```

## Mobile App Prototype (Android / Kivy)

In addition to the standalone Python CLI core (`ijrap_public_sealer.py`), this repository includes a lightweight **Kivy mobile prototype** (`main.py`) featuring:
- **Duress & Decoy PIN Vault:** Operational protection against forced device unlocking (`1234` standard vault / `9999` decoy empty view).
- **Chained Hash Timestamping & Post-Quantum Signatures:** Pure-Python `SHA3-512` + Lamport-OTS signing linked across sequential evidence bundles.
- **Automated APK Pipeline:** Configured via `buildozer.spec` and GitHub Actions (`.github/workflows/main.yml`).

To run the mobile UI locally on a desktop for testing:
```bash
pip install -r requirements.txt
python main.py
```

## Roadmap & Open Collaboration

We welcome security engineers, mobile developers, and civic-tech contributors to open **Issues** or **Pull Requests** on the following milestones:
- **Hardware-Backed Attestation:** Bridging our `libProofMode` CSV metadata and Ed25519 device keys with hardware-backed Android Keystore / StrongBox attestation.
- **Native Hardware Bridge:** Replacing desktop simulation fallbacks with native Android camera, microphone, and GPS sensor streams.
- **Post-Quantum Standardization:** Integrating NIST-standardized PQ signature schemes (ML-DSA / SLH-DSA) alongside our Ed25519 and hash-based chaining.
- **Independent Verification CLI (`verify_and_unpack.py`):** Providing a standalone auditor tool to verify `.ijrap_certificate.json`, `.ots` proofs, and decrypt `.ijrap.enc` blocks.

## License & Contact

- **License:** Released under the **GNU AGPLv3** open-source license (an enterprise tier is also available for institutional clients).
- **Contact:** `ijraplabs@proton.me` | `imoadze1@gmail.com`
