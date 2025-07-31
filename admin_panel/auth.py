from typing import Optional, Sequence

from starlette.requests import Request
from starlette.responses import Response
from starlette_admin.auth import AdminConfig, AdminUser, AuthProvider
from starlette_admin.exceptions import FormValidationError, LoginFailed

from configreader import config



users = {
    "root": {
        "name": "Root Admin",
        "roles": [
            "read",
            "create",
            "edit",
            "delete",
            "action_make_published",
            "root",
        ],
    },
    "admin": {
        "name": "Admin",
        "roles": [
            "read",
            "create",
            "edit",
            "delete",
            "action_make_published",
        ],
    },
}


class MyAuthProvider(AuthProvider):
    """
    This is for demo purpose, it's not a better
    way to save and validate user credentials
    """

    def __init__(
        self,
        login_path: str = "/login",
        logout_path: str = "/logout",
        allow_paths: Optional[Sequence[str]] = None,
        allow_routes: Optional[Sequence[str]] = None,
    ):
        self.login_path = login_path
        self.logout_path = logout_path
        self.allow_paths = allow_paths
        self.allow_routes = allow_routes
        super().__init__()

    async def login(
        self,
        username: str,
        password: str,
        remember_me: bool,
        request: Request,
        response: Response,
    ) -> Response:
        if len(username) < 3:
            raise FormValidationError(
                {"username": "Ensure username has at least 03 characters"}
            )
        if (
            username in users or username == config.admin_panel_login
        ) and password == config.admin_panel_password:
            request.session.update({"username": username})
            return response

        raise LoginFailed("Invalid username or password")

    async def is_authenticated(self, request) -> bool:
        # admin_model = await repo.user_repo.get_admin_by_login(request.session.get("username", None))
        if request.session.get("username", None) in users:
            """
            Save current `user` object in the request state. Can be used later
            to restrict access to connected user.
            """
            request.state.user = users.get(request.session["username"])
            return True

        return False

    def get_admin_config(self, request: Request) -> AdminConfig:
        user = request.state.user  # Retrieve current user
        custom_logo_url = None
        if user.get("company_logo_url", None):
            custom_logo_url = request.url_for("static", path=user["company_logo_url"])
        return AdminConfig(
            logo_url=custom_logo_url,
        )

    def get_admin_user(self, request: Request) -> AdminUser:
        user = request.state.user  # Retrieve current user
        photo_url = None
        if user.get("avatar") is not None:
            photo_url = request.url_for("static", path=user["avatar"])
        return AdminUser(username=user["name"], photo_url=photo_url)

    async def logout(self, request: Request, response: Response) -> Response:
        request.session.clear()
        return response