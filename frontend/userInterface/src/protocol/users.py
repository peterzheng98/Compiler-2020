from flask_login import UserMixin
import requests
import json
from .config import PathConfig

path = PathConfig


class UserStruct(UserMixin):
    username = ''
    userid = ''
    userpasswd = ''
    useruuid = 'N/A'
    privilege = 0

    def __init__(self, userID, userPassword):
        self.userid = userID
        self.userpasswd = userPassword
        self.username = ''
        self.useruuid = 'N/A'
        self.privilege = 0
        try:
            user_json = {
                'stu_id': self.userid,
                'stu_password': self.userpasswd
            }
            r = requests.post(path.loginPath, data=json.dumps(user_json), timeout=5)
            if r.json()['code'] == 200:
                self.username = r.json()['message']['name']
                self.privilege = 1 if r.json()['message']['uuid'][0] == 'u' else (
                    2 if r.json()['message']['uuid'][0] == 'r' else 0)
                self.useruuid = r.json()['message']['uuid']

        except Exception as ident:
            pass

    @property
    def is_authenticated(self):
        return self.useruuid != 'N/A'

    def get_id(self):
        return self.useruuid

    def __repr__(self):
        return '{}-{}-{}-{}'.format(self.username, self.userpasswd, self.privilege, self.useruuid)

    def isValid(self):
        return self.useruuid != 'N/A'

def fetchUserByID(uuid):
    try:
        user_json = {
            'stu_id': uuid,
            'stu_password': '123123'
        }
        if uuid == 'N/A':
            return None
        r = requests.post(path.fetchUuidPath, data=json.dumps(user_json), timeout=2)
        if r.json()['code'] == 200:
            return UserStruct(r.json()['message']['uid'], r.json()['message']['password'])
        return None
    except Exception as ident:
        return None