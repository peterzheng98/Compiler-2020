#!python3
from flask_wtf import FlaskForm
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from wtforms import *


class LoginForm(FlaskForm):
    userid = StringField(
        'StuID', validators=[DataRequired()], render_kw={
            'class': 'form-control monospace',
            'placeholder': 'Your Student ID'
        }
    )

    userpassword = PasswordField(
        'Password', validators=[DataRequired()], render_kw={
            'class': 'form-control monospace',
            'placeholder': 'Your Password'
        }
    )

    submit = SubmitField(
        'Login', render_kw={
            'class': "btn btn-primary",
            'id': "submit_login"
        }
    )


class RegistrationForm(FlaskForm):
    userid = StringField(
        'StuID', validators=[DataRequired()],
        render_kw={
            'class': 'form-control monospace',
            'placeholder': 'Your Student ID',
        }
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired()],
        render_kw={
            'class': 'form-control monospace',
            'placeholder': 'Password',
        }
    )
    password2 = PasswordField(
        'Repeat Password',
        validators=[DataRequired(), EqualTo('password')],
        render_kw={
            'class': 'form-control monospace',
            'placeholder': 'Password Again',
        }
    )
    email = StringField(
        'Email',
        validators=[DataRequired(), Email()],
        render_kw={
            'class': 'form-control monospace',
            'placeholder': 'Your Email Address',
        }
    )
    student_name = StringField(
        'Your real name',
        validators=[DataRequired()],
        render_kw={
            'class': 'form-control monospace',
            'placeholder': 'Your Name',
        }
    )
    repo_url = StringField(
        'Repo',
        validators=[DataRequired()],
        render_kw={
            'class': 'form-control monospace',
            'placeholder': 'Your Repository URL',
        }
    )
    submit = SubmitField(
        'Register',
        render_kw={
            'class': "btn btn-primary",
        }
    )


class ModifyPasswordForm(FlaskForm):
    old_password = PasswordField(
        'Old Password',
        validators=[DataRequired()],
        render_kw={
            'class': 'form-control monospace',
            'placeholder': 'Whatever',
        }
    )

    password = PasswordField(
        'New Password',
        validators=[DataRequired()],
        render_kw={
            'class': 'form-control monospace',
            'placeholder': 'Whatever',
        }
    )

    password2 = PasswordField(
        'Repeat Password',
        validators=[DataRequired(), EqualTo('password')],
        render_kw={
            'class': 'form-control monospace',
            'placeholder': 'Whatever',
        }
    )

    submit = SubmitField(
        'Confirm',
        render_kw={
            'class': "btn btn-primary",
        }
    )
