from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, Regexp
from wtforms.widgets import TextInput


class RegisterForm(FlaskForm):
    """
    Form for user registration with username and password validation.

    Fields:
        - username: Required, 3–20 characters.
        - password: Required, min 8 chars, includes upper, lower, digit, special char.
        - submit: Register button.
    """
    username: StringField = StringField(
        'Username',
        validators=[
            DataRequired(),
            Length(min=3, max=20, message="Username must be between 3 and 20 characters.")
        ]
    )

    password: PasswordField = PasswordField(
        'Password',
        validators=[
            DataRequired(),
            Length(min=8, message="Password must be at least 8 characters."),
            Regexp(
                r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]+$',
                message=(
                    "Password must include at least one lowercase letter, one uppercase letter, "
                    "one digit, and one special character (@$!%*?&)."
                )
            )
        ]
    )

    submit: SubmitField = SubmitField('Register')


class LoginForm(FlaskForm):
    """
    Basic login form with username and password fields.

    Fields:
        - username: Required.
        - password: Required.
        - submit: Submit button.
    """
    username: StringField = StringField("Username", validators=[DataRequired()])
    password: PasswordField = PasswordField("Password", validators=[DataRequired()])
    submit: SubmitField = SubmitField("Submit")


class PropertySearchForm(FlaskForm):
    """
    Search form to filter properties based on multiple criteria.

    Fields:
        - city: Optional city field with JS autocomplete.
        - district: Optional district.
        - price_min / price_max: Price range in Euros.
        - size_min / size_max: Property size range in m².
        - number_of_rooms: Minimum number of rooms.
        - price_m2_min / price_m2_max: Price per m² range.
        - submit: Search button.
    """
    city: StringField = StringField(
        "City",
        widget=TextInput(),
        render_kw={"id": "city-input", "autocomplete": "off"}
    )

    district: StringField = StringField("District", validators=[Optional()])

    price_min: IntegerField = IntegerField("Min Price (€)", validators=[Optional(), NumberRange(min=1)])
    price_max: IntegerField = IntegerField("Max Price (€)", validators=[Optional(), NumberRange(min=1)])

    size_min: IntegerField = IntegerField("Min Size (m²)", validators=[Optional(), NumberRange(min=1)])
    size_max: IntegerField = IntegerField("Max Size (m²)", validators=[Optional(), NumberRange(min=1)])

    number_of_rooms: IntegerField = IntegerField("Number of Rooms", validators=[Optional(), NumberRange(min=1)])

    price_m2_min: IntegerField = IntegerField("Min Price/m2 (€)", validators=[Optional(), NumberRange(min=1)])
    price_m2_max: IntegerField = IntegerField("Max Price/m2 (€)", validators=[Optional(), NumberRange(min=1)])

    submit: SubmitField = SubmitField('Search')