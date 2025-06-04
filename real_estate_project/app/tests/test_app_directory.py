# Tests for the app directory
import json
from datetime import datetime

import pytest
from bson.objectid import ObjectId
from werkzeug.datastructures import MultiDict
from ..forms import RegisterForm, LoginForm, PropertySearchForm
from ..main import app, mongo, User, bcrypt
from ..database import load_user


# Tests for database.py and extensions.py

@pytest.fixture(scope="module")
def test_client():
    #Setup Flask test client
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False  # Disable CSRF for testing
    app.config["LOGIN_DISABLED"] = False
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture
def test_user():
    #Setup a test user in the database
    password_plain = "Password@123"
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
    # Verify password hashing and checking with bcrypt
    valid = bcrypt.check_password_hash(test_user["password"], "Password@123")
    invalid = bcrypt.check_password_hash(test_user["password"], "wrongpassword")

    assert valid is True
    assert invalid is False


def test_load_user_returns_none_when_user_not_found():
    non_existent_id = str(ObjectId())
    result = load_user(non_existent_id)
    assert result is None


def test_user_class(test_user):
    # Test User class initialization
    user_obj = User(test_user)
    assert user_obj.id == str(test_user["_id"])
    assert user_obj.username == test_user["username"]


##################################################################################################

# Test for forms.py

# Simulate a basic POST request for testing
@pytest.fixture
def app_context():
    # from ..database import app
    app.config["WTF_CSRF_ENABLED"] = False  # Disable CSRF for tests
    with app.test_request_context(method="POST"):
        yield


# -------- RegisterForm Tests --------
def test_register_form_valid(app_context):
    form = RegisterForm(data={"username": "testuser", "password": "Test@123"})
    assert form.validate() is True


def test_register_form_missing_username(app_context):
    form = RegisterForm(data={"password": "Test@123"})
    assert form.validate() is False
    assert "username" in form.errors


def test_register_form_short_username(app_context):
    form = RegisterForm(data={"username": "ab", "password": "Test@123"})
    assert form.validate() is False
    assert "username" in form.errors


# -------- LoginForm Tests --------
def test_login_form_valid(app_context):
    form = LoginForm(data={"username": "user", "password": "Test@123"})
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

##################################################################################################

# Test flask_aruodas.py

def test_index(test_client):
    with app.test_client() as client:
        response = client.get('/')
        assert response.status_code == 200


def test_logout(test_client, test_user):
    response = test_client.post("/login", data={
        "username": test_user["username"],
        "password": "Password@123"
    }, follow_redirects=True)
    assert response.status_code == 200

    # Now, call the logout route
    response = test_client.get("/logout", follow_redirects=True)

    # Check that we are redirected to the index page
    assert response.status_code == 200
    html = response.data.decode()
    assert "<title>Index" in html or "Welcome" in html


def test_register(test_client):
    username = "newuser"
    response = test_client.post("/register", data={
        "username": username,
        "password": "Password@123"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert mongo.db.users.find_one({"username": "newuser"})
    # cleanup
    mongo.db.users.delete_one({"username": username})


def test_login_success(test_client, test_user):
    response = test_client.post("/login", data={
        "username": test_user["username"],
        "password": "Password@123"
    }, follow_redirects=True)

    assert b"Search" in response.data or response.status_code == 200


def test_login_failure(test_client):
    response = test_client.post("/login", data={
        "username": "nonexistent",
        "password": "wrongpass"
    }, follow_redirects=True)

    html = response.data.decode()
    assert response.status_code == 200
    assert '<form' in html  #Still on login page


def test_analyze_median_valid(test_client, test_user):
    test_client.post("/login", data={
        "username": test_user["username"],
        "password": "Password@123"
    })

    response = test_client.post("/analyze_median", json={
        "field": "price",
        "city": "",
        "limit": 5
    })

    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_analyze_median_not_valid(test_client, test_user):
    test_client.post("/login", data={
        "username": test_user["username"],
        "password": "Password@123"
    })

    response = test_client.post("/analyze_median", json={
        "field": "random",
        "city": "",
        "limit": 5
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "Invalid field"


def test_autocomplete_city(test_client, test_user):
    test_client.post("/login", data={
        "username": test_user["username"],
        "password": "Password@123"
    })

    response = test_client.get("/autocomplete/city")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_save_search_correct(test_client, test_user):
    test_client.post("/login", data={
        "username": test_user["username"],
        "password": "Password@123"
    })
    # Prepare query JSON
    query = {
        "filter": {"city": "Vilnius"},
        "sort": {"price": -1}
    }

    # Call save_search route (adjust route name/path if needed)
    response = test_client.post("/save_search", json={
        "query": query,
        "name": "Test Search"
    })

    assert response.status_code == 200
    assert response.get_json()["message"] == "Search saved!"
    mongo.db.saved_searches.delete_many({"user_id": str(test_user["_id"])})


def test_save_search_missing_name_and_query(test_client, test_user):
    test_client.post("/login", data={
        "username": test_user["username"],
        "password": "Password@123"
    })

    # Missing name
    response = test_client.post("/save_search", json={"query": {}})
    assert response.status_code == 400
    assert response.get_json()["error"] == "Search name is required"

    # Missing query
    response = test_client.post("/save_search", json={"name": "Test"})
    assert response.status_code == 400
    assert response.get_json()["error"] == "Query is missing"


def test_register_user_duplicate(test_client):
    username = "duplicateuser"
    password = "Password@123"

    # First registration should succeed
    response = test_client.post("/register", data={
        "username": username,
        "password": password
    }, follow_redirects=True)

    assert response.status_code == 200
    assert mongo.db.users.find_one({"username": username})

    # Second registration should flash a warning and redirect
    response = test_client.post("/register", data={
        "username": username,
        "password": password
    }, follow_redirects=True)

    # Check for the flash message in the response
    html = response.data.decode()
    assert "Username already exists" in html

    # Cleanup
    mongo.db.users.delete_one({"username": username})


def test_search_no_filters(test_client):
    response = test_client.post("/search", data={})
    assert response.status_code == 200
    assert b"results" in response.data or b"No results found" in response.data


def test_search_city_filter(test_client):
    response = test_client.post("/search", data={"city": "Vilnius"})
    assert response.status_code == 200
    assert b"Vilnius" in response.data


def test_search_full_filters(test_client):
    data = {
        "city": "Vilnius",
        "district": "Naujamiestis",
        "price_min": 150000,
        "price_max": 300000,
        "size_min": 50,
        "size_max": 120,
        "price_m2_min": 1000,
        "price_m2_max": 5000,
        "number_of_rooms": 2
    }
    response = test_client.post("/search", data=data)
    assert response.status_code == 200
    assert b"Vilnius" in response.data


def test_analyze_median_city_filter_applied(test_client, test_user):
    # Log in user
    test_client.post("/login", data={
        "username": test_user["username"],
        "password": "Password@123"
    })

    # Analyze median with a city filter
    response = test_client.post("/analyze_median", json={
        "field": "price",
        "city": "Vilnius"
    })

    assert response.status_code == 200
    data = response.get_json()

    # Ensure only Vilnius results are returned
    assert all(item["city"] == "Vilnius" for item in data)


def test_analyze_median_empty_data_returns_empty_list(test_client, test_user):
    # Ensure no data for this city exists
    mongo.db.properties.delete_many({"city": "Mažeikiai"})

    test_client.post("/login", data={
        "username": test_user["username"],
        "password": "Password@123"
    })

    response = test_client.post("/analyze_median", json={
        "field": "price",
        "city": "Mažeikiai"
    })

    assert response.status_code == 200
    assert response.get_json() == []


def test_my_searches_requires_login(test_client):
    # Make sure no user is logged in
    test_client.get("/logout", follow_redirects=True)
    response = test_client.get("/my_searches", follow_redirects=True)
    assert b"Login" in response.data


def test_my_searches_logged_in(test_client, test_user):
    test_client.post("/login", data={
        "username": test_user["username"],
        "password": "Password@123"
    })
    response = test_client.get("/my_searches")
    assert response.status_code == 200
    assert b"My Saved Searches" in response.data

def test_analysis_page_requires_login(test_client):
    # Make sure no user is logged in
    test_client.get("/logout", follow_redirects=True)
    response = test_client.get("/analysis_page", follow_redirects=True)
    assert b"Login" in response.data

def test_analysis_page_logged_in(test_client, test_user):
    test_client.post("/login", data={
        "username": test_user["username"],
        "password": "Password@123"
    })
    response = test_client.get("/analysis_page")
    assert response.status_code == 200
    assert b"Interactive Chart" in response.data

def test_rerun_saved_search_success(test_client, test_user):
    test_client.post("/login", data={
        "username": test_user["username"],
        "password": "Password@123"
    })

    # Example saved query: a simple MongoDB query dict encoded as JSON string
    saved_query = json.dumps({"city": "Vilnius"})

    response = test_client.post("/rerun_search", data={
        "query": saved_query
    })

    assert response.status_code == 200
    # Should render the 'search.html' template with results
    assert b"search" in response.data.lower()  # crude check


def test_rerun_saved_search_invalid_json(test_client, test_user):
    test_client.post("/login", data={
        "username": test_user["username"],
        "password": "Password@123"
    })

    # Send invalid JSON string for query
    response = test_client.post("/rerun_search", data={
        "query": "not a json"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Failed to parse saved query" in response.data

def test_delete_search_success(test_client, test_user):
    collection = mongo.db.saved_searches

    # Log in the user
    test_client.post("/login", data={
        "username": test_user["username"],
        "password": "Password@123"
    }, follow_redirects=True)

    # Get logged-in user ID from session
    with test_client.session_transaction() as sess:
        logged_in_user_id = sess.get('_user_id')
        print(f"Logged in user ID: {logged_in_user_id}")

    # Insert search tied to the logged-in user
    search_doc = {
        "user_id": logged_in_user_id,
        "name": "Test Search",
        "query": {"filter": {"city": "Vilnius"}, "sort": {"price": -1}},
        "timestamp": datetime.utcnow()
    }
    inserted = collection.insert_one(search_doc)
    search_id = inserted.inserted_id

    # Delete the search
    response = test_client.post(f"/delete_search/{search_id}", follow_redirects=True)

    # Assert deletion success
    assert b"Search deleted successfully" in response.data
    assert mongo.db.saved_searches.find_one({"_id": search_id}) is None

def test_delete_search_failure(test_client, test_user):
    collection = mongo.db.saved_searches

    # Log in the user
    test_client.post("/login", data={
        "username": test_user["username"],
        "password": "Password@123"
    }, follow_redirects=True)

    # Get logged-in user ID from session
    with test_client.session_transaction() as sess:
        logged_in_user_id = sess.get('_user_id')
        print(f"Logged in user ID: {logged_in_user_id}")

    # Insert search tied to a DIFFERENT user (to cause deletion failure)
    fake_user_id = "random_stuff"  # Not the logged-in user ID
    search_doc = {
        "user_id": fake_user_id,
        "name": "Test Search",
        "query": {"filter": {"city": "Vilnius"}, "sort": {"price": -1}},
        "timestamp": datetime.utcnow()
    }
    inserted = collection.insert_one(search_doc)
    search_id = inserted.inserted_id

    # Attempt to delete with logged-in user (should fail)
    response = test_client.post(f"/delete_search/{search_id}", follow_redirects=True)

    # Check that the failure message is in the response
    assert b"Failed to delete search." in response.data

    # Confirm the document still exists in DB (not deleted)
    assert mongo.db.saved_searches.find_one({"_id": search_id}) is not None




def test_autocomplete_district_no_city(test_client, test_user):
    test_client.post("/login", data={
        "username": test_user["username"],
        "password": "Password@123"
    })
    response = test_client.get("/autocomplete/district?q=Cent")
    assert response.status_code == 200
    assert response.get_json() == []


def test_autocomplete_district_with_city(test_client, test_user):
    test_client.post("/login", data={
        "username": test_user["username"],
        "password": "Password@123"
    })

    # Assuming your test db has some entries with city "Vilnius"
    response = test_client.get("/autocomplete/district?city=Vilnius&q=Cent")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)