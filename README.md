# IJRAP Security: Multi-Stream Forensic Truth-Preservation Core

**Founding Author & Sovereign Copyright Holder:** ADZE Kossivi Edem (IJRAP LABS / IJRAP Media)  
**Academic Reference:** Zenodo: https://zenodo.org/record/23139273 |
**ORCID:**  https://orcid.org/0009-0009-0018-6734 
**Status:** Open-Source Public Reference Implementation (GNU AGPLv3)

---

## Mission & Overview

The core mission of **IJRAP Security** is to secure empirical field data at its source using cryptographic fingerprints. Designed to counter deepfakes, metadata tampering, and hostile field conditions (zero-internet, risk of seizure), it transforms standard devices into tamper-proof evidence vaults by uniting investigative reporting with forensic science.

Our strategic focus is on independent journalists, citizen reporters, whistleblowers, and NGOs who need mathematically verifiable chains of custody. Furthermore, IJRAP Labs ensures privacy by automating data minimization in strict compliance with GDPR regulations and collecting field data offline within encrypted structures.

## Core Technical Capabilities

- **4-Pillar Evidence Sealing:** Binds live audio, video, photo, and written testimony (with GPS coordinates and UTC timestamps) into a single cryptographic block.
- **Hybrid Post-Quantum Cryptography:** Uses classical SHA-256 alongside quantum-resistant SHA-3-256 (Keccak-256) hashing.
- **WORM Immutability:** Locks files in read-only mode (`0o444`) immediately upon capture to prevent post-capture alterations.
- **Offline-First Resilience:** Operates completely offline without reliance on commercial cloud providers.

## Prerequisites

This project relies exclusively on the **Python standard library**. No external dependencies or installations via `pip` are required.

- **Python 3.8 or higher** must be installed on your machine.
- To verify your Python installation, open your terminal or command prompt and run:
  ```bash
  python --version
  ```
- If Python is not installed, download it from the official website: [python.org](https://python.org)

## Installation

1. **Clone the repository** (or download and extract the ZIP archive):
   ```bash
   git clone https://github.com/ijrapmedia/ijrap-security-public.git
   
   ```

2. **Navigate to the project directory:**
   ```bash
   cd ijrap-security-public
   ```

*(No additional installation steps are required).*

## Usage

Launch the forensic sealer by running the main script with Python:

- **On Windows:**
  ```bash
  python ijrap_public_sealer.py
  ```

- **On macOS / Linux:**
  ```bash
  python3 ijrap_public_sealer.py
  ```
## Mobile App Prototype (Android / Kivy)

In addition to the standalone Python CLI core (`ijrap_public_sealer.py`), this repository includes a lightweight **Kivy mobile prototype** (`main.py`) featuring:
- **Duress & Decoy PIN Vault:** Operational protection against forced device unlocking (`1234` standard vault / `9999` decoy empty view).
- **Chained Hash Timestamping & Post-Quantum Signatures:** Pure-Python `SHA3-512` + Lamport-OTS signing linked across sequential evidence bundles.
- **Automated APK Pipeline:** Configured via `buildozer.spec` and GitHub Actions (`.github/workflows/main.yml`).

To run the mobile UI locally on a desktop for testing:
```bash
pip install kivy==2.3.0
python main.py
```

## Roadmap & Open Collaboration

We welcome security engineers, mobile developers, and civic-tech contributors to open **Issues** or **Pull Requests** on the following milestones:
- **ProofMode / Guardian Project Interoperability:** Bridging our 4-pillar investigation bundles (synchronized media + written narrative + witness consent) with `libProofMode` metadata and hardware-backed Android Keystore attestation.
- **Native Hardware Bridge:** Replacing desktop simulation fallbacks with native Android camera, microphone, and GPS sensor streams.
- **Post-Quantum Standardization:** Integrating NIST-standardized PQ signature schemes (ML-DSA / SLH-DSA) alongside our hash-based chaining.
  
## License & Contact

- **License:** Released under the **GNU AGPLv3** open-source license (an enterprise tier is also available for institutional clients).
- **Contact:** `ijraplabs@proton.me` | `imoadze1@gmail.com`
