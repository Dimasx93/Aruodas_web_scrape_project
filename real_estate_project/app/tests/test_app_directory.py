#Tests for the app directory
import pytest
from bson.objectid import ObjectId
from werkzeug.datastructures import MultiDict
from ..database import app, mongo, User, load_user, bcrypt
from ..forms import RegisterForm, LoginForm, PropertySearchForm

#Tests for database.py and extensions.py

@pytest.fixture(scope="module")
def test_client():
    #Setup Flask test client
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False  #Disable CSRF for testing
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture
def test_user():
    #Setup a test user in the database
    password_plain = "testpassword123"
    password_hash = bcrypt.generate_password_hash(password_plain).decode('utf-8')

    user_data = {
        "username": "testuser",
        "password": password_hash,
    }
    inserted = mongo.db.users.insert_one(user_data)
    user_data["_id"] = inserted.inserted_id

    yield user_data  #Provide test data to the test

    # Clean up after test
    mongo.db.users.delete_one({"_id": inserted.inserted_id})


def test_mongo_connection():
    #Check that the database is connected and name is correct
    assert mongo.db.name == "aruodas_apartments"


def test_user_loader(test_user):
    #Test the Flask-Login user loader
    loaded_user = load_user(str(test_user["_id"]))
    assert loaded_user is not None
    assert loaded_user.username == test_user["username"]
    assert isinstance(loaded_user, User)


def test_password_hashing_and_check(test_user):
    #Verify password hashing and checking with bcrypt
    valid = bcrypt.check_password_hash(test_user["password"], "testpassword123")
    invalid = bcrypt.check_password_hash(test_user["password"], "wrongpassword")

    assert valid is True
    assert invalid is False


def test_load_user_returns_none_when_user_not_found():
    non_existent_id = str(ObjectId())
    result = load_user(non_existent_id)
    assert result is None

def test_user_class(test_user):
    #Test User class initialization
    user_obj = User(test_user)
    assert user_obj.id == str(test_user["_id"])
    assert user_obj.username == test_user["username"]

##################################################################################################

#Test for forms.py

#Simulate a basic POST request for testing
@pytest.fixture
def app_context():
    from ..database import app
    app.config["WTF_CSRF_ENABLED"] = False  #Disable CSRF for tests
    with app.test_request_context(method="POST"):
        yield

# -------- RegisterForm Tests --------
def test_register_form_valid(app_context):
    form = RegisterForm(data={"username": "testuser", "password": "testpwrd"})
    assert form.validate() is True

def test_register_form_missing_username(app_context):
    form = RegisterForm(data={"password": "testpwrd"})
    assert form.validate() is False
    assert "username" in form.errors

def test_register_form_short_username(app_context):
    form = RegisterForm(data={"username": "ab", "password": "testpwrd"})
    assert form.validate() is False
    assert "username" in form.errors


# -------- LoginForm Tests --------
def test_login_form_valid(app_context):
    form = LoginForm(data={"username": "user", "password": "pass"})
    assert form.validate() is True

def test_login_form_missing_password(app_context):
    form = LoginForm(data={"username": "user"})
    assert form.validate() is False
    assert "password" in form.errors


# -------- PropertySearchForm Tests --------
def test_property_search_form_partial_input(app_context):
    form = PropertySearchForm(data={"city": "Vilnius", "price_min": 10000})
    assert form.validate() is True

def test_property_search_form_invalid_price_range(app_context):
    form = PropertySearchForm(formdata=MultiDict({"price_min": "-50"}))
    assert form.validate() is False
    assert "price_min" in form.errors

def test_property_search_form_all_fields_valid(app_context):
    form = PropertySearchForm(data={
        "city": "Kaunas",
        "district": "Centras",
        "price_min": 10000,
        "price_max": 200000,
        "size_min": 30,
        "size_max": 100,
        "number_of_rooms": 3,
        "price_m2_min": 1000,
        "price_m2_max": 4000
    })
    assert form.validate() is True