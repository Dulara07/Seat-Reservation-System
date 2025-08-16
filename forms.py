from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo

class RegisterForm(FlaskForm):
    name = StringField('Full name', validators=[DataRequired(), Length(min=2)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField('Confirm', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ReserveForm(FlaskForm):
    date = DateField('Date', validators=[DataRequired()], format='%Y-%m-%d')
    time_slot = SelectField('Time slot', choices=[('morning', 'Morning'), ('afternoon', 'Afternoon')])
    seat_id = SelectField('Seat', coerce=int)
    submit = SubmitField('Reserve')
