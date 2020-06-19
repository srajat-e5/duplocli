from flask import Flask, jsonify, make_response, redirect, request, session
import json
import requests
from flask_cors import CORS
from flask_session import Session
import os
from datetime import datetime

app = Flask(__name__)
SESSION_COOKIE_NAME = 'duplo_auth_proxy_session'
SESSION_TYPE = 'filesystem'
SESSION_FILE_DIR = '/project/flask_cookie'
secret = os.environ.get('FLASK_APP_SECRET')
SECRET_KEY = secret.encode()

app.config.from_object(__name__)

CORS(app)
Session(app)

# rules_detail = os.environ.get('ACCESS_RULES')
# rules_detail = rules_detail.replace("'", '"')
# rules = []
# if rules_detail:
#     rules = json.loads(rules_detail)

# allowed_email_ids = os.environ.get('ALLOWED_EMAIL_IDS')
# allowed_email_id_list = []

# if allowed_email_ids:
#     allowed_email_id_list = allowed_email_ids.split(";")

class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route('/duplo_auth')
def welcome():
    return jsonify({
            'messsage': "Flask app is running",   # from cognito pool
        })

@app.route("/duplo_auth/login", endpoint='login', methods=['GET', 'POST'])
def login():
    is_allowed = False
    queryParam = ""
    for param in request.args.keys():
        tempQuery = param + "=" + request.args.get(param)
        if queryParam:
            queryParam = queryParam + "&" + tempQuery
        else:
            queryParam = "?" + tempQuery

    if request.args.get('duplo_sso_token'):
        session['duplo_sso_token'] = request.args.get('duplo_sso_token')
    elif request.form and request.form.get('duplo_sso_token'):
        session['duplo_sso_token'] = request.form.get('duplo_sso_token')

    if 'duplo_sso_token' in session and session['duplo_sso_token']:
        # print("login -- using token from session")
        is_allowed = authorize_user(session['duplo_sso_token'])
        if is_allowed:
            session['authorized_on'] = str(datetime.utcnow())
    else:
        # print("going to other block")
        raise InvalidUsage('No Permission to view this page', status_code=403)

    if is_allowed:
        response = make_response(redirect('/' + queryParam))
        return response
    else:
        raise InvalidUsage('No Permission to view this page', status_code=403)

@app.route('/duplo_auth/auth')
def api_private():
    # print("auth function invoked")
    is_allowed = False
    if 'duplo_sso_token' in session and session['duplo_sso_token']:
        if 'authorized_on' in session and session['authorized_on']:
            last_authorized_time_delta = datetime.utcnow() - datetime.strptime(session['authorized_on'], '%Y-%m-%d %H:%M:%S.%f')
            if last_authorized_time_delta.total_seconds() < 300:
                is_allowed = True

        if not is_allowed:
            print("Doing reauth on" , str(datetime.utcnow()))
            is_allowed = authorize_user(session['duplo_sso_token'])
            if is_allowed:
                session['authorized_on'] = str(datetime.utcnow())
    else:
        raise InvalidUsage('No Permission to view this page', status_code=403)

    if is_allowed:
        return jsonify({
            'valid_user': True,   # from cognito pool
        })
    else:
        raise InvalidUsage('No Permission to view this page', status_code=403)


def authorize_user(duplo_sso_token):
    duplo_auth_url = os.environ.get('DUPLO_AUTH_URL')
    tenant_id = os.environ.get('TENANT_ID')
    is_allowed = False

    duplo_auth_headers = {
        'Authorization': 'Bearer ' + duplo_sso_token
    }
    duplo_userinfo_response = requests.get(duplo_auth_url + "/admin/GetTenantConfigData/" + tenant_id, headers=duplo_auth_headers)
    userinfo = {}
    if duplo_userinfo_response.status_code == 200:
        print("Userinfo api success response", duplo_userinfo_response.json())
        is_allowed = True

    return is_allowed

