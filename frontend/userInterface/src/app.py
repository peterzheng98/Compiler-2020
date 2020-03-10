from flask import Flask, render_template, Blueprint, redirect, flash

from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import *
from flask_login import current_user, login_required, login_user, logout_user, LoginManager
import requests as HTTPReq
import subprocess
import json

from forms import LoginForm, RegistrationForm
from tools import validator, gitTools
from protocol.users import UserStruct, fetchUserByID
from protocol.config import PathConfig

path = PathConfig()

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


@app.route('/judge/detail/<string:judgeid>/<string:judgepid>')
@login_required
def judge_detail(judgeid: str, judgepid: str):
    if not validator.isAllDigits(judgeid):
        flash('Invalid operation: {} is an invalid code.'.format(judgeid))
        return redirect('/judge/list/0')
    # fetch the general result
    try:
        dat = {
            'uuid': judgeid,
            'repo': judgepid
        }
        r = HTTPReq.post(path.fetchStatusBrief, timeout=2, data=json.dumps(dat))
        if r.json()['code'] != 200:
            return render_template('judge_detail.html',
                                   webconfig={'title': 'Details for #{} - Compiler 2020'.format(judgeid)},
                                   content_title='Details for Record #{}'.format(judgeid),
                                   commit_message='Error occurred in fetching the message.\nTechnical Information:\n{}'.format(
                                       r.json()['message']),
                                   header_list=['#', 'Phase', 'Test case', 'Verdict', 'Compiling Time',
                                                'Execution Cycles'],
                                   record_list=[],
                                   judge_list=[],
                                   prev_page=0)
        judge_list = [None]
        judge_list[0] = ('0-Build', '1', 100.0) if 'Success' in r.json()['message']['buildResult'] else (
        '0-Build', '0', 0.0)
        passed_attr = 'btn btn-sm btn-success custom-xsmall-font custom-bold-font'
        failed_attr = 'btn btn-sm btn-danger custom-bold-font custom-xsmall-font'
        std_font_attr = 'custom-small-font'
        dat2 = {
            'uuid': judgepid,
            'repo': '123'
        }
        r2 = HTTPReq.post(path.fetchJudgeResultDetail, timeout=5, data=json.dumps(dat2))
        print('==>{}'.format(r2.json()))
        record_list = []
        if r2.json()['code'] != 200 or r2.json()['message'] is None:
            record_list = []
        else:
            for Idx, D in enumerate(r2.json()['message']):
                sub_list = [(std_font_attr, '', Idx), (std_font_attr, '',
                                                       '1-Semantic' if D[0] == '1' else '2-Codegen' if D[
                                                                                                           0] == '2' else '3-Optimize' if
                                                       D[0] == '3' else 'Unknown'), (std_font_attr, '', D[1])]
                if D[2][0] == '0':
                    sub_list.append((passed_attr, '', 'passed'))
                else:
                    sub_list.append((failed_attr, '', 'failed'))
                compileTime, executionCycle, JudgeTime = D[3].split('/')
                sub_list.append((std_font_attr, '', '{:.2f}s'.format(float(compileTime))))
                sub_list.append((std_font_attr, '', executionCycle))
                sub_list.append((std_font_attr, '', JudgeTime))
                record_list.append(sub_list)

            positive = {}
            negative = {}
            for elem in record_list:
                if elem[1][2] not in positive.keys():
                    positive[elem[1][2]] = 0
                    negative[elem[1][2]] = 0
                if elem[3][2] == 'passed':
                    positive[elem[1][2]] = positive[elem[1][2]] + 1
                else:
                    negative[elem[1][2]] = negative[elem[1][2]] + 1
            for k, v in positive.items():
                judge_list.append((k, '{}'.format(v), '{:.2f}'.format(100.0 * v / (v + negative[k])),
                                   '{}'.format(negative[k]), '{:.2f}'.format(100.0 - 100.0 * v / (v + negative[k]))))
        return render_template('judge_detail.html',
                               webconfig={'title': 'Details for #{} - Compiler 2020'.format(judgeid)},
                               content_title='Details for Record #{}'.format(judgeid),
                               commit_message=r.json()['message']['gitMessage'],
                               header_list=['#', 'Phase', 'Test case', 'Verdict', 'Compiling', 'Execution Cycles',
                                            'Judge Time'],
                               record_list=record_list,
                               judge_list=judge_list,
                               prev_page=0, builtMessage=r.json()['message']['buildMessage'].replace('\\n', '\n'))
    except Exception as identifier:
        return render_template('judge_detail.html',
                               webconfig={'title': 'Details for #{} - Compiler 2020'.format(judgeid)},
                               content_title='Details for Record #{}'.format(judgeid),
                               commit_message='Error occurred in fetching the message.',
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


@app.route('/ranking')
@login_required
def get_ranking():
    table_header = ['Name', 'Score']
    for i in range(100):
        table_header.append('#{}'.format(i))
    return render_template('ranking.html', webconfig={'title': 'Ranking - Compiler 2020'},
                           content_title='Ranking', table_header=table_header, table_content=[])


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect('/')
    registerForm = RegistrationForm()
    if request.method == 'GET':
        return render_template('register.html', webconfig={'title': 'Register - Compiler 2020'},
                               registerForm=registerForm)
    else:
        userid = request.form.get('userid')
        password = request.form.get('password')
        password2 = request.form.get('password2')
        email = request.form.get('email')
        student_name = request.form.get('student_name')
        repo_url = request.form.get('repo_url')
        if '@' not in email:
            flash('Your email is invalid.')
            return render_template('register.html', webconfig={'title': 'Register - Compiler 2020'},
                                   registerForm=registerForm)
        if password != password2:
            flash('Password doesn\'t match')
            return render_template('register.html', webconfig={'title': 'Register - Compiler 2020'},
                                   registerForm=registerForm)
        reg_data = {
            'stu_id': userid,
            'stu_password': password,
            'stu_repo': repo_url,
            'stu_name': student_name,
            'stu_email': email
        }
        try:
            r = HTTPReq.post(path.registerPath, data=json.dumps(reg_data), timeout=5)
            if r.json()['code'] != 200:
                flash('Error occurred! {}'.format(r.json()['message']))
                return render_template('register.html', webconfig={'title': 'Register - Compiler 2020'},
                                       registerForm=registerForm)
            flash('Register Successfully!')
            return redirect('/login')
        except Exception as identifier:
            flash('Error occurred! {}'.format(identifier))
            return render_template('register.html', webconfig={'title': 'Register - Compiler 2020'},
                                   registerForm=registerForm)


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')


if __name__ == '__main__':
    app.run('127.0.0.1', 5000)
