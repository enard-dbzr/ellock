from flask import jsonify
from flask_restful import Resource, abort
from flask_jwt_extended import jwt_required

from ells import hardware


class OpenResource(Resource):
    method_decorators = [jwt_required()]

    def get(self):
        return jsonify({"successfully": hardware.open()})
