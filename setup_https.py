"""
Setup HTTPS untuk Flask dengan self-signed certificate
Untuk development/testing - tidak untuk production
"""
from flask import Flask
import ssl
import os
from pathlib import Path

def create_self_signed_cert():
    """Create self-signed certificate untuk HTTPS."""
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from datetime import datetime, timedelta
        
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Create certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "ID"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Jakarta"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Jakarta"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Face Recognition"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                x509.IPAddress(ipaddress.IPv4Address("10.22.10.131")),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        
        # Save certificate and key
        cert_dir = Path("certs")
        cert_dir.mkdir(exist_ok=True)
        
        cert_path = cert_dir / "cert.pem"
        key_path = cert_dir / "key.pem"
        
        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        with open(key_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        print(f"Certificate created: {cert_path}")
        print(f"Private key created: {key_path}")
        return str(cert_path), str(key_path)
        
    except ImportError:
        print("cryptography library not installed. Installing...")
        import subprocess
        subprocess.check_call(["pip", "install", "cryptography"])
        return create_self_signed_cert()
    except Exception as e:
        print(f"Error creating certificate: {e}")
        return None, None

if __name__ == "__main__":
    import ipaddress
    cert_path, key_path = create_self_signed_cert()
    if cert_path and key_path:
        print("\n" + "="*60)
        print("HTTPS Certificate Created!")
        print("="*60)
        print("\nTo run with HTTPS:")
        print("  python -m api.web_interface_https")
        print("\nOr update web_interface.py to use SSL context")
        print("="*60)

