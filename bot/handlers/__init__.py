from .start import router as start_router
from .task_callbacks import router as task_callbacks_routers
from .ai_handlers import router as ai_handlers_router

routers_list = [start_router, task_callbacks_routers, ai_handlers_router]
