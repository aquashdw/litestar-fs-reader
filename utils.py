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
    secret_key = PrivateKey.generate()
    secret_path.write_bytes(secret_key.encode())

    public_path = key_path / 'public_key'
    public_path.unlink(missing_ok=True)
    public_key = secret_key.public_key
    public_path.write_text(public_key.encode().hex())

    hand_path = key_path / 'handshake'
    hand_path.unlink(missing_ok=True)
    hand_key = str(uuid.uuid4()).replace('-', '')
    hand_path.write_text(hand_key)


decoder = None


def get_decoder():
    global decoder
    if decoder:
        return decoder
    key_path = Path(config.KEY_DIR)
    secret_path = key_path / 'private_key'
    if not secret_path.exists():
        print('secret key not found, creating')
        create_key(True)

    secret_key = PrivateKey(secret_path.read_bytes())
    decoder = SealedBox(secret_key)
    return decoder


def get_handshake():
    key_path = Path(config.KEY_DIR)
    hand_path = key_path / 'handshake'
    return hand_path.read_text()


def create_test_message(message):
    public_hex = (Path(config.KEY_DIR) / 'public_key').read_text()
    public_key = PublicKey(bytes.fromhex(public_hex))
    encrypter = SealedBox(public_key)
    print(f'encrypting message to hex: {message}')
    return encrypter.encrypt(message.encode()).hex()


if __name__ == '__main__':
    # create_key(True)
    decoder = get_decoder()

    # test encrypt handshake + session pair
    handshake = get_handshake()
    session_uuid = uuid.uuid4()
    message = create_test_message(str(handshake).replace('-', '') + ':' + str(session_uuid).replace('-', ''))
    print(f'handshake: {message}')
    # decrypted = decoder.decrypt(bytes.fromhex(message))
    # print(decrypted)
    # print(decrypted.decode())

    # test session id encrypt
    session_id = str(session_uuid).replace('-', '')
    encrypted = create_test_message(session_id)
    print(f'sessionid encrypted: {encrypted}')

    # test decrypt failure
    # print(decoder.decrypt(b'randomtextrandomtextrandomtextrandomtextasdfasdf'))
