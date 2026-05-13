from litestar import Litestar, Router
from litestar.middleware import DefineMiddleware

from auth.components import NamelessSessionAuthMiddleware
from auth.routes import handlers as auth_handlers
from fs.routes import handlers as fs_handlers
from init import init

fs_router = Router(
    path='/fs',
    route_handlers=[*fs_handlers]
)

auth_router = Router(
    path='/auth',
    route_handlers=[*auth_handlers]
)

auth_middleware = DefineMiddleware(NamelessSessionAuthMiddleware, exclude=['/auth/session'])

app = Litestar(
    route_handlers=[fs_router, auth_router],
    middleware=[auth_middleware],
    on_startup=[init],
)
