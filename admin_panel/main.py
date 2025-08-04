import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles
from starlette_admin import I18nConfig
from starlette_admin.contrib.sqla import Admin
from starlette_admin.i18n import SUPPORTED_LOCALES

from admin_panel.auth import MyAuthProvider
from admin_panel.views import model_views
from bot.db.base import engine
from configreader import config

static_dir = os.path.join("admin_panel", "static")
os.makedirs(static_dir, 0o777, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan for FastAPI app"""
    yield


app = FastAPI(
    debug=True,
    routes=[
        Mount("/static", app=StaticFiles(directory=static_dir), name="static"),
    ],
    lifespan=lifespan,
)

# app.add_middleware(
#     TrustedHostMiddleware,
#     allowed_hosts=["admin-panel.mushrooms.biz.ua", "*.mushrooms.biz.ua"]
# )

admin = Admin(
    engine,
    title="Адмін-панель",
    base_url="/",
    statics_dir=static_dir,
    auth_provider=MyAuthProvider(),
    middlewares=[
        Middleware(SessionMiddleware, secret_key=config.admin_panel_session_secret)
    ],
    i18n_config=I18nConfig(default_locale="ru", language_switcher=SUPPORTED_LOCALES),
    favicon_url="https://tabler.io/favicon.ico",
)

for model_view in model_views:
    admin.add_view(model_view)

# Mount admin to your app
admin.mount_to(app)
