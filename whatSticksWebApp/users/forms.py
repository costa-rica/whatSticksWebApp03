from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed #used for image uploading
from wtforms import StringField, PasswordField, SubmitField, BooleanField\
    , TextAreaField, DateTimeField, FloatField, DateField, TimeField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, InputRequired, Optional
from wtforms_sqlalchemy.fields import QuerySelectField
from whatSticksWebApp.models import Users, Posts
from flask_login import current_user
from datetime import datetime
from whatSticksWebApp import db
from wtforms.widgets import PasswordInput

# from wtforms.validators import Optional

# def make_optional(field):
#     field.validators.insert(0, Optional())


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[Optional()])
    email = StringField('Email',
                        validators=[InputRequired(),Email()])
    password = PasswordField('Password', validators=[InputRequired()])
    # confirm_password = PasswordField('Confirm Password',
    #                                  validators=[InputRequired(), EqualTo('password')])
    submit = SubmitField('Sign up')
    # gender = StringField('gender')
    # height = StringField('height')
    birthdate=DateField('Birthdate', validators=[Optional()])
    show_password = BooleanField('Show password')

    # def validate_username(self, username):
        # user=User.query.filter_by(username=username.data).first()
        # if user:
            # raise ValidationError('That username already taken.')

    def validate_email(self, email):
        user=Users.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email already taken.')
    





class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    # password = PasswordField('Password', render_kw={'placeholder':'test'}, validators=[DataRequired()])
    password = StringField('Password', widget=PasswordInput(hide_value=False), validators=[DataRequired()])
    
    # remember = BooleanField('Remember me')
    show_password = BooleanField('Show password')
    submit = SubmitField('Login')


class UpdateAccountForm(FlaskForm):
    username = StringField('Username')
    email = StringField('Email',
                        validators=[DataRequired(),Email()])
    picture = FileField('Update Profile Picture', validators = [FileAllowed(['jpg','png'])])
    submit = SubmitField('Update')

    # def validate_username(self, username):
        # if username.data != current_user.username:
            # user=User.query.filter_by(username=username.data).first()
            # if user:
                # raise ValidationError('That username already taken.')

    def validate_email(self, email):
        if email.data != current_user.email:
            user=Users.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email already taken.')

class RequestResetForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(),Email()])
    submit = SubmitField('Request password reset')


    def validate_email(self, email):
        user=Users.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('There is no account with that email. You must register first.')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')