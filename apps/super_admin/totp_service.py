"""
super_admin/totp_service.py — TOTP (Google Authenticator) for Super Admin.
Uses pyotp — pip install pyotp (add to requirements.txt).
"""
import pyotp
import base64


def generate_totp_secret() -> str:
    """Generate a new base32 TOTP secret."""
    return pyotp.random_base32()


def get_totp_uri(secret: str, email: str, issuer: str = 'DADCARE Control') -> str:
    """Return the otpauth:// URI for QR code generation."""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=issuer)


def verify_totp(secret: str, code: str) -> bool:
    """Verify a 6-digit TOTP code. Allows 1 window drift (30s each side)."""
    if not secret or not code:
        return False
    totp = pyotp.TOTP(secret)
    return totp.verify(code.strip(), valid_window=1)


def generate_qr_data_url(totp_uri: str) -> str:
    """
    Generate a base64 QR code PNG data URL.
    Requires: pip install qrcode[pil]
    Falls back to returning the URI if qrcode not installed.
    """
    try:
        import qrcode
        import io
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color='black', back_color='white')
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode()
        return f"data:image/png;base64,{b64}"
    except ImportError:
        return totp_uri
