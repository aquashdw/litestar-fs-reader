from litestar import Litestar, Router

import auth_routes
from fs.routes import handlers as fs_handlers
from init import init

fs_router = Router(
    path='/fs',
    route_handlers=[*fs_handlers]
)

auth_router = Router(
    path='/auth',
    route_handlers=[*auth_routes.handlers]
)

app = Litestar(
    route_handlers=[fs_router, auth_router],
    on_startup=[init],
)
