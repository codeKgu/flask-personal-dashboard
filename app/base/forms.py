from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length

## login and registration


class LoginForm(FlaskForm):
    username = StringField('Username', id='username_login', validators=[DataRequired(),
                                                                        Length( min=5, max=20)])
    password = PasswordField('Password', id='pwd_login')


class CreateAccountForm(FlaskForm):
    username = StringField('Username', id='username_create')
    email = StringField('Email')
    password = PasswordField('Password', id='pwd_create')
