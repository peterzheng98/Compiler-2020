from flask import Flask, render_template, Blueprint, redirect, flash

from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import *
from flask_login import current_user, login_required, login_user, logout_user, LoginManager
import requests as HTTPReq
import subprocess

from forms import LoginForm
from tools import validator
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
login_manager.login_view = 'auth.login'


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


@app.route('/compiler_list')
@login_required
def compiler_list():
    try:
        r = HTTPReq.get(path.getUserListPath, timeout=2)
        if r.json()['code'] == 200:
            table_content = [v for k, v in r.json()['message'].items()]
            return render_template('lists.html', webconfig={'title': 'Compiler Lists - Compiler 2020'},
                                   content_title='Compiler Lists',
                                   table_content=table_content)
        else:
            return render_template('lists.html', webconfig={'title': 'Compiler Lists - Compiler 2020'},
                                   content_title='Error occurred.', table_content=[])
    except Exception as identifier:
        print('-> Error: {}'.format(identifier))
        return render_template('lists.html', webconfig={'title': 'Compiler Lists - Compiler 2020'},
                               content_title='Error occurred.', table_content=[])


@app.route('/products/<product>')
def products(product):
    return 'product: ' + str(product)


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')


if __name__ == '__main__':
    app.run('127.0.0.1', 5000)
