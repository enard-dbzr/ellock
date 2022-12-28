from flask_restful import Api
from flask_jwt_extended import JWTManager

from ells.models import db_session
from ells.models.users import User

from ells.api.lock_resource import OpenResource
from ells.api.user_resource import LoginResource

jwt = JWTManager()


@jwt.user_identity_loader
def user_identity_lookup(user):
    return user.id


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    db = db_session.create_session()
    return db.query(User).filter_by(id=identity).first()


def create_api(app):
    api = Api(app)
    jwt.init_app(app)

    api.add_resource(LoginResource, '/api/login')
    api.add_resource(OpenResource, '/api/open')
