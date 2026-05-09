from litestar import Litestar, Router

import auth_routes
import fs_routes
from init import init

fs_router = Router(
    path='/fs',
    route_handlers=[*fs_routes.handlers]
)

auth_router = Router(
    path='/auth',
    route_handlers=[*auth_routes.handlers]
)

app = Litestar(
    route_handlers=[fs_router, auth_router],
    on_startup=[init],
)
