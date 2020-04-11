from flask import Flask, render_template, Blueprint, redirect, flash

from flask_bootstrap import Bootstrap
from flask_nav.elements import *
from flask_login import current_user, login_required, login_user, logout_user, LoginManager
import requests as HTTPReq
import base64
import json
import sys
import time
import ansiconv
import subprocess

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


@app.route('/base64/detail/<string:raw_id_1>/<string:raw_id_2>')
def base64_decode(raw_id_1, raw_id_2):
    std_str = '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/tonsky/FiraCode@1.207/distr/fira_code.css"><style>.code-font-medium {font-family: \'Fira Code\', monospace;font-size: medium;}</style><style>'
    try:
        str_raw_html = base64.b64decode((''.join(open('static/datalogs/{}_{}.txt'.format(raw_id_1, raw_id_2), 'r').readlines())).encode()).decode().replace('\n', '<br>')
        html_conv = ansiconv.to_html(str_raw_html).replace('ansi37', '')
        str_html = '<body class="code-font-medium">{}</body></html>'.format(html_conv)
        st_css = ansiconv.base_css()
        return std_str + st_css + '</style></head>' + str_html
    except Exception as ident:
        return 'Error occurred. {}'.format(ident)


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
        record_list = []
        if r2.json()['code'] != 200 or r2.json()['message'] is None:
            record_list = []
        else:
            for Idx, D in enumerate(r2.json()['message']):
                result = '/'.join(D[2].split('/')[1:])
                subWorkID = D[4].replace('_', '/')
                aref = '/base64/detail/{}'.format(subWorkID)
                open('static/datalogs/{}.txt'.format(D[4]), 'w').write(result)
                sub_list = [
                    (std_font_attr, aref, Idx),
                    (std_font_attr, '', '1-Semantic' if D[0] == '1' else '2-Codegen' if D[0] == '2' else '3-Optimize' if
                                                         D[0] == '3' else 'Unknown'),
                    (std_font_attr, '', D[1])
                ]
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
                               commit_message=base64.b64decode(r.json()['message']['gitMessage'].encode()).decode(),
                               header_list=['#', 'Phase', 'Test case', 'Verdict', 'Compiling', 'Execution Cycles',
                                            'Judge Time'],
                               record_list=record_list,
                               judge_list=judge_list,
                               prev_page=0,
                               builtMessage=base64.b64decode(r.json()['message']['buildMessage'].encode()).decode().replace('\\n', '\n'))
    except Exception as identifier:
        return render_template('judge_detail.html',
                               webconfig={'title': 'Details for #{} - Compiler 2020'.format(judgeid)},
                               content_title='Details for Record #{}'.format(judgeid),
                               commit_message='Error occurred in fetching the message.',
                               header_list=['#', 'Phase', 'Test case', 'Verdict', 'Compiling Time', 'Execution Cycles'],
                               record_list=[],
                               judge_list=[],
                               prev_page=0)


def getSystemStatus():
    return_list = []
    command = [
        ('Server Name', ['uname','-n']), ('Kernel Release', ['uname', '-r']), ('Kernel Version', ['uname', '-v'])
    ]
    for i in command:
        try:
            r = subprocess.check_output(i[1], timeout=1)
            return_list.append([i[0], r.decode()])
        except Exception:
            return_list.append([i[0], 'N/A'])
    return_list.append(['NeoFetch Information', ' '])
    try:
        r = subprocess.check_output(['neofetch', '--stdout'], timeout=1)
        r = r.decode().strip().split('\n')[2:-1]
        r = [i.split(':') for i in r]
        return_list = return_list + r
    except Exception:
        return_list.append(['Neofetch info', 'N/A'])
    return return_list



@app.route('/status')
@login_required
def show_server_status():
    sys_header = ['Key','Value']
    sys_content = getSystemStatus()
    return render_template(
        'server_status.html', webconfig={'title': 'Server Status - Compiler 2020'},
        sys_table_header = sys_header, sys_table_content=sys_content
    )


@app.route('/status/compile')
@login_required
def show_server_status_compile():
    html_code = '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/tonsky/FiraCode@1.207/distr/fira_code.css"><style>.code-font-medium {font-family: \'Fira Code\', monospace;font-size: small;}</style></head>'
    body_code = '<body class="code-font-medium"><h2>Build Queue</h2>{}</body></html>'
    try:
        r = HTTPReq.get(path.fetchServerStatus, timeout=2)
        if 'error-compile' in r.json()['message'].keys():
            body_code = body_code.format('Currently Unavailable')
            return html_code + body_code
        table_header = '<table><thead><th>#</th> <th>ID</th> <th>Repo</th> <th>GitHash</th> <th>Submit Time</th> </thead>{}</table>'
        table_content = '<tbody>{}</tbody>'
        table_cell = []
        cnt = 0
        d = json.loads(r.json()['message']['compile'])
        for k, v in d.items():
            cell_content = '<td>&nbsp;&nbsp;{}&nbsp;&nbsp;</td>'
            cell_list = [
                '<tr>',
                cell_content.format(cnt),
                cell_content.format(v['uuid'][1:]),
                cell_content.format(v['repo']),
                cell_content.format(v['githash']),
                cell_content.format(str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(k))))),
                '</tr>'
            ]
            table_cell.append(''.join(cell_list))
            cnt = cnt + 1
        return html_code + body_code.format(table_header.format(table_content.format(''.join(table_cell))))
    except Exception as ident:
        body_code = body_code.format('Currently Unavailable. {}'.format(ident))
        return html_code + body_code


@app.route('/status/semantic')
@login_required
def show_server_status_semantic():
    html_code = '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/tonsky/FiraCode@1.207/distr/fira_code.css"><style>.code-font-medium {font-family: \'Fira Code\', monospace;font-size: small;}</style></head>'
    body_code = '<body class="code-font-medium"><h2>Semantic Queue</h2><h3>Person View</h3>{}</body></html>'
    try:
        r = HTTPReq.get(path.fetchServerStatus, timeout=2)
        if 'error-compile' in r.json()['message'].keys():
            body_code = body_code.format('Currently Unavailable')
            return html_code + body_code
        table_header = '<table><thead><th>#</th> <th>ID</th> <th>Repo</th> <th>GitHash</th> <th>Status</th> </thead>{}</table>'
        table_content = '<tbody>{}</tbody>'
        table_cell = []
        d_list = json.loads(r.json()['message']['semantic'])
        json.dump(r.json(), open('rmp.json', 'w'), ensure_ascii=False)
        for cnt, d in enumerate(d_list):
            cell_content = '<td>&nbsp;&nbsp;{}&nbsp;&nbsp;</td>'
            pass_list = [i.split('_')[0] for i in d['success']] if d['success'] is not None else []
            fail_list = [i.split('_')[0] for i in d['fail']] if d['fail'] is not None else []
            cell_list = [
                '<tr>',
                cell_content.format(cnt),
                cell_content.format(d['uuid'][1:]),
                cell_content.format(d['repo']),
                cell_content.format(d['githash']),
                cell_content.format('Passed: {} / Failed: {} / Running: {} / Pending: {}'.format(len(pass_list), len(fail_list), len(d['running_set']), len(d['pending']))),
                '</tr>'
            ]
            table_cell.append(''.join(cell_list))

        return html_code + body_code.format(table_header.format(table_content.format(''.join(table_cell))))
    except Exception as ident:
        body_code = body_code.format('Currently Unavailable. {}'.format(ident))
        return html_code + body_code


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
    if sys.argv[1] == 'deploy':
        app.run('0.0.0.0', 10567, debug=False)
    else:
        app.run('127.0.0.1', 5000)
