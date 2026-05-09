from typing import Annotated

from litestar import post
from litestar.exceptions import HTTPException
from litestar.params import Parameter
from nacl.exceptions import CryptoError

from utils import get_decoder, get_handshake

authenticated = set()


@post('/session', status_code=204)
async def create_session(
        bearer: Annotated[str, Parameter(header='Authorization')],
) -> None:
    if bearer is None or not bearer.startswith('Bearer '):
        raise HTTPException(status_code=401)

    token = bearer[7:]
    try:
        decrypted = get_decoder().decrypt(bytes.fromhex(token)).decode()
        handshake, session_id = decrypted.split(':')
        if handshake != get_handshake():
            raise HTTPException(status_code=401)
        # TODO: manage session id with more functionalities
        authenticated.add(session_id)
        print(authenticated)
        return None
    except CryptoError:
        raise HTTPException(status_code=401)


handlers = [create_session]
