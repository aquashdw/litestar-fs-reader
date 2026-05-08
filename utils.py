import mimetypes
import uuid
from pathlib import Path
from typing import AsyncGenerator

from nacl.public import PrivateKey, SealedBox, PublicKey

import config


def get_mime_type(filename: str) -> str:
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or 'application/octet-stream'


async def file_streamer(file_path: Path) -> AsyncGenerator[bytes, None]:
    """Streams a file from disk in chunks to minimize memory usage."""
    chunk_size = 65536  # 64KB
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            yield chunk


def create_key(overwrite=False):
    # configure save location
    key_path = Path(config.KEY_DIR)
    if key_path.exists() and not overwrite:
        print('key exists')
        return
    key_path.mkdir(exist_ok=True)
    secret_path = key_path / 'private_key'
    secret_path.unlink(missing_ok=True)

    public_path = key_path / 'public_key'
    public_path.unlink(missing_ok=True)

    secret_key = PrivateKey.generate()
    secret_path.write_bytes(secret_key.encode())

    public_key = secret_key.public_key
    public_path.write_text(public_key.encode().hex())


def get_decoder():
    key_path = Path(config.KEY_DIR)
    secret_path = key_path / 'private_key'
    if not secret_path.exists():
        print('secret key not found, creating')
        create_key(True)

    secret_key = PrivateKey(secret_path.read_bytes())
    return SealedBox(secret_key)


def create_test_message():
    public_hex = (Path(config.KEY_DIR) / 'public_key').read_text()
    public_key = PublicKey(bytes.fromhex(public_hex))
    encrypter = SealedBox(public_key)
    session_uuid = uuid.uuid4()
    print(f'created message: {str(session_uuid).replace('-', '')}')
    session_id = session_uuid.bytes
    return encrypter.encrypt(session_id).hex()


decoder = get_decoder()
print(decoder.decrypt(bytes.fromhex(create_test_message())).hex())
