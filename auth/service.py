from litestar.connection import ASGIConnection
from litestar.exceptions import NotAuthorizedException
from litestar.middleware import AbstractAuthenticationMiddleware, AuthenticationResult

from utils import get_decoder


class NamelessSessionAuthMiddleware(AbstractAuthenticationMiddleware):
    authenticated = set()

    async def authenticate_request(self, connection: ASGIConnection) -> AuthenticationResult:
        auth_header = connection.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise NotAuthorizedException()

        token = auth_header.split()[1]
        session_id = get_decoder().decrypt(bytes.fromhex(token)).decode()
        if not session_id in NamelessSessionAuthMiddleware.authenticated:
            raise NotAuthorizedException()
        return AuthenticationResult(True, None)
