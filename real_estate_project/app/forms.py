# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Length, Optional, NumberRange

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Submit")

class PropertySearchForm(FlaskForm):

    city = StringField("City", validators=[Optional()])
    district = StringField("District", validators=[Optional()])

    price_min = IntegerField("Min Price (€)", validators=[Optional(), NumberRange(min=1)])
    price_max = IntegerField("Max Price (€)", validators=[Optional(), NumberRange(min=1)])

    size_min = IntegerField("Min Size (m²)", validators=[Optional(), NumberRange(min=1)])
    size_max = IntegerField("Max Size (m²)", validators=[Optional(), NumberRange(min=1)])

    number_of_rooms = IntegerField("Number of Rooms", validators=[Optional(), NumberRange(min=1)])

    price_m2_min = IntegerField("Min Price/m2 (€)", validators=[Optional(), NumberRange(min=1)])
    price_m2_max = IntegerField("Max Price/m2 (€)", validators=[Optional(), NumberRange(min=1)])

    submit = SubmitField('Search')