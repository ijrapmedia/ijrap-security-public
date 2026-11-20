import io
import json
from datetime import datetime, timezone
from c2pa import Builder, Signer, SigningAlg

class IJRAPC2PABridge:
    """
    Pont d'interopérabilité C2PA Content Credentials (100 % en mémoire RAM).
    Embarque l'empreinte forensique SHA3-512 et l'ID de chaîne IJRAP
    dans un manifeste standardisé C2PA.
    """

    def __init__(self, cert_pem: bytes, key_pem: bytes, tsa_url: str = None):
        """
        Initialise le signataire C2PA avec un certificat X.509 (ES256 / Ed25519).
        """
        self.signer = Signer.from_info(
            alg=SigningAlg.ES256,
            sign_cert=cert_pem,
            private_key=key_pem,
            tsa_url=tsa_url,
        )

    def sign_stream_in_memory(
        self,
        media_bytes: bytes,
        mime_type: str,
        title: str,
        investigator_id: str,
        bundle_id: str,
        sha3_512_digest: str,
        gps_coords: tuple[float, float] | None = None,
    ) -> bytes:
        """
        Prend un média brut en RAM, attache un manifeste C2PA signé
        et retourne le média scellé en octets (zéro écriture disque).
        """
        manifest_definition = {
            "claim_generator": "IJRAP_Security_Core/3.0",
            "title": title,
            "assertions": [
                {
                    "label": "c2pa.actions",
                    "data": {
                        "actions": [
                            {
                                "action": "c2pa.created",
                                "when": datetime.now(timezone.utc).isoformat(),
                                "softwareAgent": "IJRAP LABS Forensic Core",
                            }
                        ]
                    },
                },
                {
                    # Assertion personnalisée reliant C2PA au bloc monolithique .ijrap
                    "label": "org.ijrap.forensic.seal",
                    "data": {
                        "investigator_id": investigator_id,
                        "bundle_id": bundle_id,
                        "sha3_512_digest": sha3_512_digest,
                        "gps_coords": list(gps_coords) if gps_coords else None,
                    },
                },
            ],
        }

        builder = Builder(manifest_definition)
        source_stream = io.BytesIO(media_bytes)
        dest_stream = io.BytesIO()

        builder.sign(
            signer=self.signer,
            format=mime_type,
            source=source_stream,
            dest=dest_stream,
        )

        return dest_stream.getvalue()
      
