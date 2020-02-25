from flask import Flask, render_template, Blueprint, redirect, flash

from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import *
from flask_login import current_user, login_required, login_user, logout_user, LoginManager
import requests as HTTPReq
import subprocess
import json

from forms import LoginForm
from tools import validator, gitTools
from protocol.users import UserStruct, fetchUserByID
from protocol.config import PathConfig

path = PathConfig()

auth = Blueprint('auth', __name__)
app = Flask(__name__)
app.config["SECRET_KEY"] = 'pikachu-loves-watermelon'
Bootstrap(app)

# Should be closed if it is deployed
app.debug = True
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_message = 'Please login first.'
login_manager.login_message_category = 'error'
login_manager.session_protection = 'strong'
login_manager.login_view = '/'


@login_manager.user_loader
def load_user(stu_id):
    return fetchUserByID(stu_id)


@app.route('/')
def index():
    return render_template('index.html', webconfig={'title': 'Compiler 2020'})


@app.route('/login', methods=['GET', 'POST'])
def login_app():
    if current_user.is_authenticated:
        return redirect('/')
    loginForm = LoginForm()
    if request.method == 'GET':
        return render_template('login.html', webconfig={'title': 'Login'}, loginForm=loginForm)
    else:
        stu_id = request.form.get('userid')
        stu_password = request.form.get('userpassword')
        user = UserStruct(stu_id, stu_password)
        login_user(user)
        if not user.isValid():
            flash('Login Failed! Please check your account.')
            return redirect('/login')
            pass
        return redirect('/')


@app.route('/judge/detail/<string:judgeid>')
@login_required
def judge_detail(judgeid: str):
    if not validator.isAllDigits(judgeid):
        flash('Invalid operation: {} is an invalid code.'.format(judgeid))
        return redirect('/judge/list/0')
    passed_attr = 'btn-sm btn-success custom-xsmall-font custom-bold-font'
    failed_attr = 'btn-sm btn-warning custom-bold-font custom-xsmall-font'
    return render_template('judge_detail.html', webconfig={'title': 'Details for #{} - Compiler 2020'.format(judgeid)},
                           content_title='Details for Record #{}'.format(judgeid),
                           commit_message='12345\n\n123\n\n123->',
                           header_list=['#', 'Phase', 'Test case', 'Verdict', 'Compiling Time', 'Execution Cycles'],
                           record_list=[],
                           judge_list=[],
                           prev_page=0)


@app.route('/judge/list/<string:page>')
@login_required
def judge_list(page: str):
    try:
        if not validator.isAllDigits(page):
            return redirect('/judge/list/0')
        current_page = int(page)
        current_idx = int(page) * 15
        send_data = [current_idx, 15]
        r = HTTPReq.post(path.fetchStatusPath, timeout=2, data=json.dumps(send_data))
        prev_page = max(0, current_page - 1)
        next_page = current_page + 1
        if r.json()['code'] == 200:
            max_length = min(15, len(r.json()['message']))
            table_content = [r.json()['message'][str(i)] for i in range(max_length)]
            table_header = ['#', 'StuID', 'Submit Hash', 'Stage', 'Judge Time']
            return render_template('judge_status.html', webconfig={'title': 'Judge Lists - Compiler 2020'},
                                   content_title='Judge Status',
                                   table_content=table_content,
                                   table_header=table_header, prev_page=prev_page, next_page=next_page)
        else:
            return render_template('judge_status.html', webconfig={'title': 'Judge Lists - Compiler 2020'},
                                   content_title='Error occurred.', table_content=[], table_header=[])
    except Exception as identifier:
        print('-> Error: {}'.format(identifier))
        return render_template('judge_status.html', webconfig={'title': 'Judge Lists - Compiler 2020'},
                               content_title='Error occurred.', table_content=[], table_header=[])


@app.route('/compiler/list')
@login_required
def compiler_list():
    try:
        r = HTTPReq.get(path.getUserListPath, timeout=2)
        if r.json()['code'] == 200:
            table_content = [v for k, v in r.json()['message'].items()]
            for idx, n in enumerate(table_content):
                n[3] = int(n[3])
                n.append(validator.idx2stage(n[3]))
                n.append(validator.idx2class(n[3]))
            table_header = ['ID', 'Name', 'Repo Address', 'Stage']
            return render_template('lists.html', webconfig={'title': 'Compiler Lists - Compiler 2020'},
                                   content_title='Compiler Lists',
                                   table_content=table_content,
                                   table_header=table_header)
        else:
            return render_template('lists.html', webconfig={'title': 'Compiler Lists - Compiler 2020'},
                                   content_title='Error occurred.', table_content=[], table_header=[])
    except Exception as identifier:
        print('-> Error: {}'.format(identifier))
        return render_template('lists.html', webconfig={'title': 'Compiler Lists - Compiler 2020'},
                               content_title='Error occurred.', table_content=[], table_header=[])


@app.route('/req_judge')
@login_required
def request_judge():
    try:
        request_user_information = {
            'stu_id': current_user.useruuid,
            'stu_password': '12345'
        }
        r = HTTPReq.post(path.fetchUuidPath, data=json.dumps(request_user_information), timeout=2)
        if r.json()['code'] != 200:
            flash('Error in requesting judge, error code:{}'.format(r.json()['code']))
            return redirect('/compiler/list')
        request_judge_json = {
            'uuid': current_user.useruuid,
            'repo': r.json()['message']['userrepo']
        }
        r = HTTPReq.post(path.requestJudgePath, timeout=2, data=json.dumps(request_judge_json))
        if r.json()['code'] != 200:
            flash('Error in requesting judge, error code:{}'.format(r.json()['code']))
            return redirect('/compiler/list')
        flash('Judge in queue.')
        return redirect('/compiler/list')
    except Exception as identifier:
        flash('Error in requesting judge. Please try again later. {}'.format(identifier))
        return redirect('/compiler/list')


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')


if __name__ == '__main__':
    app.run('127.0.0.1', 5000)
