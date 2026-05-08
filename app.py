from litestar import Litestar, Router

import fs_routes
from init import init

fs_router = Router(
    path='/fs',
    route_handlers=[*fs_routes.handlers]
)

app = Litestar(
    route_handlers=[fs_router],
    on_startup=[init],
)
