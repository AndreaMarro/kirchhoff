"""Ricevute locali per legare una foto alla netlist corretta e confermata.

Nessuna immagine viene persistita: il server valida il contenuto, calcola un
digest e firma ricevute brevi con una chiave di processo. Riavviare il server
invalida le conferme precedenti, senza rendere falsa una vecchia lezione.
"""
from __future__ import annotations

import base64
from hashlib import sha256
import hmac
from io import BytesIO
import json
import re
import time

MAX_IMAGE_BYTES = 2_000_000
MAX_IMAGE_PIXELS = 40_000_000
TOKEN_LIFETIME_SECONDS = 3600
_DATA_URL = re.compile(r"^data:image/(png|jpeg|webp);base64,([A-Za-z0-9+/=]+)$")


def image_decoder_available() -> bool:
    """L'extra media è opzionale per il motore e per l'ingresso manuale."""
    try:
        from PIL import Image
    except ImportError:
        return False
    return True


def _check_dimensions(width: int, height: int) -> None:
    if not 0 < width <= 10_000 or not 0 < height <= 10_000 or width * height > MAX_IMAGE_PIXELS:
        raise ValueError("Dimensioni dell'immagine non supportate.")


def _webp_preflight(data: bytes) -> None:
    """Solo bounds: libwebp può allocare il canvas già in Image.open.

    Non attesta validità: dopo questi header serve sempre il decoder reale.
    I tre header di immagine ammessi sono VP8X, VP8 e VP8L.
    """
    if len(data) >= 25 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        if data[12:16] == b"VP8X" and len(data) >= 30:
            _check_dimensions(1 + int.from_bytes(data[24:27], "little"),
                              1 + int.from_bytes(data[27:30], "little"))
            return
        if data[12:16] == b"VP8 " and len(data) >= 30 and data[23:26] == b"\x9d\x01\x2a":
            _check_dimensions(int.from_bytes(data[26:28], "little") & 0x3fff,
                              int.from_bytes(data[28:30], "little") & 0x3fff)
            return
        if data[12:16] == b"VP8L" and data[20] == 0x2f:
            packed = int.from_bytes(data[21:25], "little")
            _check_dimensions((packed & 0x3fff) + 1, ((packed >> 14) & 0x3fff) + 1)
            return
    raise ValueError("Immagine WebP non leggibile.")


def _dimensions(kind: str, data: bytes) -> tuple[int, int]:
    """Decodifica una foto statica entro i limiti, senza riscriverne i byte.

    L'orientamento EXIF resta nell'originale: qui non si normalizza la proiezione
    né il digest. Apertura e dimensioni precedono il caricamento dei pixel;
    verify controlla la struttura, load verifica anche lo stream compresso.
    """
    expected = {"png": "PNG", "jpeg": "JPEG", "webp": "WEBP"}[kind]
    if kind == "webp":
        _webp_preflight(data)
    try:
        from PIL import Image, UnidentifiedImageError
    except ImportError:
        raise ValueError("Verifica foto non disponibile su questo server. Usa l'ingresso manuale del circuito.") from None
    try:
        with Image.open(BytesIO(data), formats=[expected]) as image:
            width, height = image.size
            _check_dimensions(width, height)
            if getattr(image, "is_animated", False):
                raise ValueError("Usa una foto statica, non un'immagine animata.")
            image.verify()
        with Image.open(BytesIO(data), formats=[expected]) as image:
            image.load()
    except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombError):
        raise ValueError("Immagine non leggibile o formato dichiarato diverso dal contenuto.") from None
    return width, height


def image_digest(image: str) -> str:
    if not isinstance(image, str) or len(image) > 2_800_000:
        raise ValueError("Usa PNG, JPEG o WebP entro 2 MB.")
    match = _DATA_URL.fullmatch(image)
    if not match:
        raise ValueError("Usa PNG, JPEG o WebP in formato immagine valido.")
    try:
        data = base64.b64decode(match.group(2), validate=True)
    except ValueError as exc:
        raise ValueError("Immagine base64 non valida.") from exc
    if not 0 < len(data) <= MAX_IMAGE_BYTES:
        raise ValueError("Usa PNG, JPEG o WebP entro 2 MB.")
    _dimensions(match.group(1), data)
    return sha256(data).hexdigest()


def _sign(payload: dict, secret: bytes) -> str:
    body = base64.urlsafe_b64encode(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).rstrip(b"=")
    signature = base64.urlsafe_b64encode(hmac.digest(secret, body, "sha256")).rstrip(b"=")
    return body.decode() + "." + signature.decode()


def _open(token: str, kind: str, secret: bytes, now: int) -> dict:
    try:
        body, signature = token.split(".", 1)
        signed = hmac.digest(secret, body.encode(), "sha256")
        actual = base64.urlsafe_b64decode(signature + "=" * (-len(signature) % 4))
        if not hmac.compare_digest(signed, actual):
            raise ValueError
        payload = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
        issued = payload["iat"]
        if payload.get("v") != 1 or payload.get("kind") != kind or not isinstance(issued, int) or not now - TOKEN_LIFETIME_SECONDS <= issued <= now + 60:
            raise ValueError
        return payload
    except (AttributeError, KeyError, TypeError, ValueError, UnicodeDecodeError):
        raise ValueError("Conferma della foto non valida o scaduta: ricontrolla il circuito.") from None


def source_receipt(image: str, secret: bytes, now: int | None = None) -> dict:
    issued = int(time.time()) if now is None else now
    digest = image_digest(image)
    return dict(source_sha256=digest, source_token=_sign(dict(v=1, kind="source", sha=digest, iat=issued), secret))


def confirm_revision(source_token: str, netlist: str, confirmed: bool, secret: bytes, now: int | None = None) -> dict:
    issued = int(time.time()) if now is None else now
    if confirmed is not True or not isinstance(netlist, str) or not netlist.strip() or len(netlist) > 16000:
        raise ValueError("Confronta la foto, correggi il circuito e conferma questa revisione.")
    source = _open(source_token, "source", secret, issued)
    circuit = sha256(netlist.encode()).hexdigest()
    token = _sign(dict(v=1, kind="confirmed", source=source["sha"], circuit=circuit, iat=issued), secret)
    return dict(source_sha256=source["sha"], circuit_sha256=circuit, confirmation_token=token,
                confirmed_at_unix=issued)


def verify_revision(token: str, netlist: str, secret: bytes, now: int | None = None) -> dict:
    issued = int(time.time()) if now is None else now
    payload = _open(token, "confirmed", secret, issued)
    if payload["circuit"] != sha256(netlist.encode()).hexdigest():
        raise ValueError("Il circuito è cambiato dopo la conferma: controlla e conferma di nuovo.")
    return dict(source_kind="image", source_sha256=payload["source"], circuit_sha256=payload["circuit"],
                confirmed_at_unix=payload["iat"])
