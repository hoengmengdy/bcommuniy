from backend.routes.auth import bp as auth
from backend.routes.users import bp as users
from backend.routes.posts import bp as posts
from backend.routes.chat import bp as chat
from backend.routes.resources import bp as resources


def register_routes(app):
    for blueprint in (auth, users, posts, chat, resources):
        app.register_blueprint(blueprint, url_prefix="/api")
