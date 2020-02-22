from flask import request
from flask import Blueprint
from flask import render_template, redirect, abort

from flask_login import LoginManager
from flask_login import login_user, logout_user
from flask_login import current_user, login_required

from .models import User, db
from .forms import RegistrationForm, LoginForm

login_manager = LoginManager()
login_manager.login_view = 'users.login'
user_app = Blueprint('users', __name__, template_folder='templates')

@login_manager.user_loader
def load_user(userid):
    return User.query.filter_by(id=userid).first()

@user_app.route('/logout')
def logout():
    logout_user()
    return redirect('/')

@user_app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == 'GET':
        return render_template('login.html', title='login')
    if request.method == 'POST':
        try:
            studentid = request.form['studentid']
            password = request.form['password']
            user = User.query.filter_by(id=studentid).first()
            if user and user.check_password(password):
                login_user(user)
                return {'info': 'success'}
            return {'info': 'Wrong id or passwd'}
        except:
            abort(406)

@user_app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == 'GET':
        return render_template('register.html', title='register')
    if request.method == 'POST':
        try:
            form = RegisterForm()
            if form.validate_on_submit():
                user = User(request.form['studentid'],
                            request.form['username'],
                            request.form['password'])
                db.session.add(user)
                db.session.commit()
                return {'info' : 'login'}
            else:
                print(form.errors)
                return {'info' : 'Input Error'}
        except:
            return {'info': 'The username or student id has existed.'}

@user_app.route('/passwd', methods=['GET', 'POST'])
@login_required
def passwd():
    if request.method == 'GET':
        return render_template('passwd.html', title='Change Password')
    if request.method == 'POST':
        try:
            if current_user.check_password(request.form['old']) and request.form['new'] == request.form['confirm']:
                user = User.query.filter_by(id=current_user.id).first()
                user.set_password(request.form['new'])
                db.session.commit()
                return render_template('success.html', title='Success', message='Change Success!!')
            return render_template('error.html', title='Error', message='Password Error')
        except:
            abort(400)