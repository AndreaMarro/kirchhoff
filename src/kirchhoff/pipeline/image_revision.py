"""Ricevute locali per legare una foto alla netlist corretta e confermata.

Nessuna immagine viene persistita: il server valida il contenuto, calcola un
digest e firma ricevute brevi con una chiave di processo. Riavviare il server
invalida le conferme precedenti, senza rendere falsa una vecchia lezione.
"""
from __future__ import annotations

import base64
from hashlib import sha256
import hmac
import json
import re
import struct
import time

MAX_IMAGE_BYTES = 2_000_000
MAX_IMAGE_PIXELS = 40_000_000
TOKEN_LIFETIME_SECONDS = 3600
_DATA_URL = re.compile(r"^data:image/(png|jpeg|webp);base64,([A-Za-z0-9+/=]+)$")


def _dimensions(kind: str, data: bytes) -> tuple[int, int]:
    if kind == "png" and data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24 and data[12:16] == b"IHDR":
        return struct.unpack(">II", data[16:24])
    if kind == "webp" and data.startswith(b"RIFF") and data[8:12] == b"WEBP" and len(data) >= 30:
        if data[12:16] == b"VP8X":
            return (1 + int.from_bytes(data[24:27], "little"), 1 + int.from_bytes(data[27:30], "little"))
        if data[12:16] == b"VP8 " and data[23:26] == b"\x9d\x01\x2a":
            return (int.from_bytes(data[26:28], "little") & 0x3fff,
                    int.from_bytes(data[28:30], "little") & 0x3fff)
        if data[12:16] == b"VP8L" and data[20] == 0x2f:
            packed = int.from_bytes(data[21:25], "little")
            return ((packed & 0x3fff) + 1, ((packed >> 14) & 0x3fff) + 1)
    if kind == "jpeg" and data.startswith(b"\xff\xd8\xff"):
        offset = 2
        while offset + 4 <= len(data):
            if data[offset] != 0xff:
                break
            marker = data[offset + 1]
            if marker in {0xd8, 0xd9}:
                offset += 2
                continue
            length = int.from_bytes(data[offset + 2:offset + 4], "big")
            if length < 2 or offset + 2 + length > len(data):
                break
            if marker in {0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7, 0xc9, 0xca, 0xcb, 0xcd, 0xce, 0xcf} and length >= 7:
                return (int.from_bytes(data[offset + 7:offset + 9], "big"),
                        int.from_bytes(data[offset + 5:offset + 7], "big"))
            offset += 2 + length
    raise ValueError("Immagine non leggibile o formato dichiarato diverso dal contenuto.")


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
    width, height = _dimensions(match.group(1), data)
    if not 0 < width <= 10_000 or not 0 < height <= 10_000 or width * height > MAX_IMAGE_PIXELS:
        raise ValueError("Dimensioni dell'immagine non supportate.")
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
