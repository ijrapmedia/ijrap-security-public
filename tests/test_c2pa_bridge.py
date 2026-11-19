import io
import json
from datetime import datetime, timedelta, timezone
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from c2pa import Reader
from c2pa_bridge import IJRAPC2PABridge


def _generate_ephemeral_es256_credentials() -> tuple[bytes, bytes]:
    """Génère une paire clé/certificat ES256 temporaire en RAM pour les tests."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "IJRAP LABS Test Signer"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "IJRAP LABS"),
    ])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc) - timedelta(minutes=1))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=1))
        .sign(private_key, hashes.SHA256())
    )
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return cert_pem, key_pem


def test_c2pa_in_memory_signing_and_verification():
    """Vérifie que le pont C2PA signe en RAM et préserve l'assertion forensique IJRAP."""
    cert_pem, key_pem = _generate_ephemeral_es256_credentials()
    bridge = IJRAPC2PABridge(cert_pem=cert_pem, key_pem=key_pem)

    # Image JPEG minimale valide (1x1 pixel) en mémoire
    minimal_jpeg = (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c"
        b"\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c"
        b"\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\xff\xc0\x00\x0b\x08\x00"
        b"\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01"
        b"\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05"
        b"\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9"
    )

    fake_sha3 = "a" * 128
    signed_bytes = bridge.sign_stream_in_memory(
        media_bytes=minimal_jpeg,
        mime_type="image/jpeg",
        title="Lome Field Test Capture",
        investigator_id="IJRAP-TG-01",
        bundle_id="IJRAP_TEST_001",
        sha3_512_digest=fake_sha3,
        gps_coords=(6.1319, 1.2228),
    )

    assert len(signed_bytes) > len(minimal_jpeg)

    # Lecture et audit du manifeste C2PA directement depuis la RAM
    reader = Reader("image/jpeg", io.BytesIO(signed_bytes))
    manifest_store = json.loads(reader.json())
    active_manifest = manifest_store["manifests"][manifest_store["active_manifest"]]

    # Vérifie que l'assertion forensique IJRAP est bien embarquée
    assertions = {a["label"]: a["data"] for a in active_manifest["assertions"]}
    assert "org.ijrap.forensic.seal" in assertions
    assert assertions["org.ijrap.forensic.seal"]["sha3_512_digest"] == fake_sha3
    assert assertions["org.ijrap.forensic.seal"]["investigator_id"] == "IJRAP-TG-01"
