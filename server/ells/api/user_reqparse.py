from flask_restful.reqparse import RequestParser

login_parser = RequestParser()
login_parser.add_argument("username", required=True)
login_parser.add_argument("password", required=True)
