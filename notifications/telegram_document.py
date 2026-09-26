import mimetypes
import os
import uuid
import urllib.request
from pathlib import Path


def _multipart(fields, files):
    boundary = "----StyleAgent" + uuid.uuid4().hex
    chunks = []
    for name, value in fields.items():
        chunks += [
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
            str(value).encode("utf-8"),
            b"\r\n",
        ]
    for name, path in files.items():
        p = Path(path)
        ctype = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
        chunks += [
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="{name}"; filename="{p.name}"\r\n'.encode(),
            f"Content-Type: {ctype}\r\n\r\n".encode(),
            p.read_bytes(),
            b"\r\n",
        ]
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), boundary


def send_document(path: str, caption: str = ""):
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        return {"ok": False, "sent": False, "reason": "Telegram 配置不完整"}

    body, boundary = _multipart(
        {"chat_id": chat_id, "caption": caption[:1000]},
        {"document": path},
    )
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendDocument",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return {"ok": True, "sent": True, "status": resp.status}
