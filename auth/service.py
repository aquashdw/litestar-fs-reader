import time

from litestar.connection import ASGIConnection
from litestar.exceptions import NotAuthorizedException
from litestar.middleware import AbstractAuthenticationMiddleware, AuthenticationResult
from redis import Redis

from singletons import redis_connection
from utils import get_decoder


class AuthRedisClient:
    def __init__(self, redis: Redis):
        self.redis = redis

    def add(self, session_id: str):
        now = time.time_ns()
        self.redis.hset('fs-session', mapping={
            session_id: now
        })
        self.redis.hexpire('fs-session', 3060, session_id)

    def __contains__(self, session_id):
        exists = self.redis.hexists('fs-session', session_id)
        if exists:
            self.redis.hexpire('fs-session', 3600, session_id)
        return exists

    def __str__(self):
        return f'<AuthRedisClient (Sessions: {self.redis.hlen("fs-session")})>'


session_manager = AuthRedisClient(redis_connection)


class NamelessSessionAuthMiddleware(AbstractAuthenticationMiddleware):
    authenticated = session_manager

    async def authenticate_request(self, connection: ASGIConnection) -> AuthenticationResult:
        auth_header = connection.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise NotAuthorizedException()

        token = auth_header.split()[1]
        session_id = get_decoder().decrypt(bytes.fromhex(token)).decode()
        if not session_id in NamelessSessionAuthMiddleware.authenticated:
            raise NotAuthorizedException()
        return AuthenticationResult(True, None)
