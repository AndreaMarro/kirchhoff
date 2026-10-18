"""Media originali sintetici: ricevuta solo dopo decode verificato."""
import base64
from hashlib import sha256
from io import BytesIO
from http.server import ThreadingHTTPServer
import importlib.util
import json
from pathlib import Path
import struct
import sys
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import zlib

import pytest
from PIL import Image
from PIL import WebPImagePlugin

from kirchhoff.pipeline.image_revision import image_digest, source_receipt


def data_url(kind, raw):
    return f"data:image/{kind};base64," + base64.b64encode(raw).decode()


def original(kind, **options):
    stream = BytesIO()
    Image.new("RGB", (3, 2), (30, 80, 120)).save(stream, format=kind.upper(), **options)
    return stream.getvalue()


@pytest.mark.parametrize("kind", ["png", "jpeg", "webp"])
def test_immagine_valida_preserva_digest_dei_byte_originali(kind):
    raw = original(kind)
    assert image_digest(data_url(kind, raw)) == sha256(raw).hexdigest()
    assert source_receipt(data_url(kind, raw), b"test-only", now=1000) == source_receipt(
        data_url(kind, raw), b"test-only", now=1000)


def test_png_di_24_byte_non_riceve_ricevuta():
    raw = b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", 1, 1)
    assert len(raw) == 24
    with pytest.raises(ValueError):
        source_receipt(data_url("png", raw), b"test-only", now=1000)


@pytest.mark.parametrize("kind", ["png", "jpeg", "webp"])
def test_file_troncato_dopo_intestazione_non_e_immagine_valida(kind):
    raw = original(kind)
    with pytest.raises(ValueError):
        image_digest(data_url(kind, raw[:-20]))


def test_png_crc_corrotto_e_rifiutato():
    raw = bytearray(original("png"))
    start = raw.index(b"IDAT")
    raw[start + 4] ^= 1
    with pytest.raises(ValueError):
        image_digest(data_url("png", bytes(raw)))


def test_mime_diverso_dai_byte_e_rifiutato():
    with pytest.raises(ValueError):
        image_digest(data_url("jpeg", original("png")))


def test_limiti_pixel_sono_applicati_prima_del_caricamento(monkeypatch):
    raw = bytearray(original("png"))
    raw[16:24] = struct.pack(">II", 9000, 9000)
    raw[29:33] = struct.pack(">I", zlib.crc32(raw[12:29]))
    def non_allocare(*args, **kwargs):
        pytest.fail("Il decoder non deve caricare pixel oltre il limite")
    monkeypatch.setattr(Image.Image, "load", non_allocare)
    with pytest.raises(ValueError):
        image_digest(data_url("png", bytes(raw)))


@pytest.mark.parametrize("chunk", ["VP8X", "VP8 ", "VP8L"])
def test_webp_oltre_limite_non_entra_nel_decoder_nativo(monkeypatch, chunk):
    width, height = 9000, 9000
    if chunk == "VP8X":
        payload = b"\0" * 4 + (width-1).to_bytes(3, "little") + (height-1).to_bytes(3, "little")
    elif chunk == "VP8 ":
        payload = b"\0" * 3 + b"\x9d\x01\x2a" + width.to_bytes(2, "little") + height.to_bytes(2, "little")
    else:
        payload = b"\x2f" + ((width-1) | ((height-1) << 14)).to_bytes(4, "little")
    body = b"WEBP" + chunk.encode() + len(payload).to_bytes(4, "little") + payload
    raw = b"RIFF" + len(body).to_bytes(4, "little") + body
    def non_allocare(*args, **kwargs):
        pytest.fail("WebP ha raggiunto il decoder nativo prima dei bounds")
    monkeypatch.setattr(WebPImagePlugin._webp, "WebPAnimDecoder", non_allocare)
    with pytest.raises(ValueError, match="Dimensioni"):
        image_digest(data_url("webp", raw))


@pytest.mark.parametrize("lossless,alpha", [(True, False), (False, False), (False, True)])
def test_webp_valide_con_header_diversi(lossless, alpha):
    stream = BytesIO()
    Image.new("RGBA" if alpha else "RGB", (3, 2), (30, 80, 120, 100) if alpha else (30, 80, 120)).save(
        stream, format="WEBP", lossless=lossless)
    raw = stream.getvalue()
    assert image_digest(data_url("webp", raw)) == sha256(raw).hexdigest()


def test_animazione_rifiutata_senza_firmare_solo_il_primo_frame():
    stream = BytesIO()
    Image.new("RGB", (3, 2), "red").save(stream, format="PNG", save_all=True,
        append_images=[Image.new("RGB", (3, 2), "blue")], duration=10, loop=0)
    with pytest.raises(ValueError):
        image_digest(data_url("png", stream.getvalue()))


def test_exif_non_riscrive_i_byte_firmati():
    exif = Image.Exif()
    exif[274] = 6
    raw = original("jpeg", exif=exif)
    assert image_digest(data_url("jpeg", raw)) == sha256(raw).hexdigest()


def test_png_storico_con_stream_corrotto_e_rifiutato():
    raw = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9b4wAAAABJRU5ErkJggg==")
    with pytest.raises(ValueError):
        image_digest(data_url("png", raw))


def test_senza_decoder_nessuna_foto_firmata_e_ingresso_testuale_disponibile(monkeypatch):
    from kirchhoff.pipeline.lesson import create_lesson
    from kirchhoff.pipeline.image_revision import image_decoder_available
    raw = original("png")
    monkeypatch.setitem(sys.modules, "PIL", None)
    assert not image_decoder_available()
    with pytest.raises(ValueError, match="Verifica foto non disponibile"):
        source_receipt(data_url("png", raw), b"test-only", now=1000)
    result = create_lesson("V1 a 0 12 volt\nR1 a 0 6 ohm\n? current R1")
    assert result["answer"]["exact"] == "2"


def test_http_firma_solo_immagini_realmente_decodificate():
    path = Path(__file__).resolve().parents[1] / "scripts/serve_student.py"
    spec = importlib.util.spec_from_file_location("serve_student_decode_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    server = ThreadingHTTPServer(("127.0.0.1", 0), module.Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    def post(image):
        return urlopen(Request(f"http://127.0.0.1:{server.server_port}/api/source",
            data=json.dumps(dict(image=image)).encode(),
            headers={"Content-Type": "application/json"}))
    try:
        png24 = original("png")[:24]
        with pytest.raises(HTTPError) as error:
            post(data_url("png", png24))
        assert error.value.code == 422
        assert "source_token" not in json.load(error.value)
        for kind in ("png", "jpeg", "webp"):
            raw = original(kind)
            with post(data_url(kind, raw)) as response:
                result = json.load(response)
            assert result["source_sha256"] == sha256(raw).hexdigest()
            assert result["source_token"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
