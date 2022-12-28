from flask import jsonify
from flask_restful import Resource, abort
from flask_jwt_extended import create_access_token

from ells.models import db_session
from ells.models.users import User

from ells.api.user_reqparse import login_parser


class LoginResource(Resource):
    def get(self):
        db = db_session.create_session()
        args = login_parser.parse_args()

        user = db.query(User).filter_by(username=args["username"]).first()

        if not user or not user.check_password(args["password"]):
            return "Wrong username or password", 401

        token = create_access_token(identity=user)
        return jsonify({"token": token})
