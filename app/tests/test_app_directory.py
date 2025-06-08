# Tests for the app directory

import json
from datetime import datetime
from typing import Generator, Dict, Any

import pytest
from bson.objectid import ObjectId
from flask.testing import FlaskClient
from werkzeug.datastructures import MultiDict
from ..forms import RegisterForm, LoginForm, PropertySearchForm
from ..main import app, mongo, User, bcrypt
from ..db_init import load_user


# -------------------------- Fixtures --------------------------

@pytest.fixture(scope="module")
def test_client() -> Generator[FlaskClient, None, None]:
    """
    Create a test client for the Flask app.
    """
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False  # Disable CSRF for testing
    app.config["LOGIN_DISABLED"] = False
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture
def test_user() -> Generator[Dict[str, Any], None, None]:
    """
    Create and yield a test user, then clean up after the test.
    """
    password_plain = "Password@123"
    password_hash = bcrypt.generate_password_hash(password_plain).decode('utf-8')

    user_data = {
        "username": "testuser",
        "password": password_hash,
    }
    inserted = mongo.db.users.insert_one(user_data)
    user_data["_id"] = inserted.inserted_id

    yield user_data  # Provide test data to the test

    # Clean up after test
    mongo.db.users.delete_one({"_id": inserted.inserted_id})


# Simulate a basic POST request for testing
@pytest.fixture
def app_context() -> Generator[None, None, None]:
    """
    Provide an application context for WTForms testing.
    """
    app.config["WTF_CSRF_ENABLED"] = False  # Disable CSRF for tests
    with app.test_request_context(method="POST"):
        yield


# -------------------------- MongoDB and User Tests --------------------------

def test_mongo_connection() -> None:
    """Test that MongoDB is connected with the expected database name."""
    assert mongo.db.name == "aruodas_apartments"


def test_user_loader(test_user: Dict[str, Any]) -> None:
    """Test if a user can be loaded by ID."""
    loaded_user = load_user(str(test_user["_id"]))
    assert loaded_user is not None
    assert loaded_user.username == test_user["username"]
    assert isinstance(loaded_user, User)


def test_password_hashing_and_check(test_user: Dict[str, Any]) -> None:
    """Validate password hashing and checking."""
    assert bcrypt.check_password_hash(test_user["password"], "Password@123")
    assert not bcrypt.check_password_hash(test_user["password"], "wrongpassword")


def test_load_user_returns_none_when_user_not_found() -> None:
    """User loader should return None for non-existent user ID."""
    assert load_user(str(ObjectId())) is None


def test_user_class(test_user: Dict[str, Any]) -> None:
    """Test the User model wrapper."""
    user_obj = User(test_user)
    assert user_obj.id == str(test_user["_id"])
    assert user_obj.username == test_user["username"]


# -------------------------- Form Validation Tests --------------------------

def test_register_form_valid(app_context: None) -> None:
    """Test that valid registration form data passes validation."""
    form = RegisterForm(data={"username": "testuser", "password": "Test@123"})
    assert form.validate()


def test_register_form_missing_username(app_context: None) -> None:
    """Form validation fails when username is missing."""
    form = RegisterForm(data={"password": "Test@123"})
    assert not form.validate()
    assert "username" in form.errors


def test_register_form_short_username(app_context: None) -> None:
    """Ensure username length requirements are enforced."""
    form = RegisterForm(data={"username": "ab", "password": "Test@123"})
    assert not form.validate()
    assert "username" in form.errors


def test_login_form_valid(app_context: None) -> None:
    """Test login form with valid data."""
    form = LoginForm(data={"username": "user", "password": "Test@123"})
    assert form.validate()


def test_login_form_missing_password(app_context: None) -> None:
    """Ensure login form fails without a password."""
    form = LoginForm(data={"username": "user"})
    assert not form.validate()
    assert "password" in form.errors


def test_property_search_form_partial_input(app_context: None) -> None:
    """Property search form should be valid with partial input."""
    form = PropertySearchForm(data={"city": "Vilnius", "price_min": 10000})
    assert form.validate()


def test_property_search_form_invalid_price_range(app_context: None) -> None:
    """Ensure price_min validation catches invalid negative value."""
    form = PropertySearchForm(formdata=MultiDict({"price_min": "-50"}))
    assert not form.validate()
    assert "price_min" in form.errors


def test_property_search_form_all_fields_valid(app_context: None) -> None:
    """Test full valid input for the property search form."""
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
    assert form.validate()


# -------------------------- Route and View Tests --------------------------

def test_index(test_client: FlaskClient) -> None:
    """Test the index route returns a 200 OK response."""
    response = test_client.get('/')
    assert response.status_code == 200


def test_logout(test_client: FlaskClient, test_user: Dict[str, Any]) -> None:
    """Test logout functionality after login."""
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


def test_register(test_client: FlaskClient) -> None:
    """Test user registration flow."""
    username = "newuser"
    response = test_client.post("/register", data={
        "username": username,
        "password": "Password@123"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert mongo.db.users.find_one({"username": "newuser"})
    # cleanup
    mongo.db.users.delete_one({"username": username})


def test_register_user_duplicate(test_client: FlaskClient) -> None:
    """Test that registering a duplicate username shows an error."""
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


def test_login_success(test_client: FlaskClient, test_user: Dict[str, Any]) -> None:
    """Test successful login."""
    response = test_client.post("/login", data={
        "username": test_user["username"],
        "password": "Password@123"
    }, follow_redirects=True)

    assert b"Search" in response.data or response.status_code == 200


def test_login_failure(test_client: FlaskClient) -> None:
    """Ensure login fails with incorrect credentials."""
    response = test_client.post("/login", data={
        "username": "nonexistent",
        "password": "wrongpass"
    }, follow_redirects=True)

    html = response.data.decode()
    assert response.status_code == 200
    assert '<form' in html  # Still on login page


# -------------------------- Analyze Median --------------------------

def test_analyze_median_valid(test_client: FlaskClient, test_user: Dict[str, Any]) -> None:
    """Test median analysis endpoint with valid input."""
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


def test_analyze_median_not_valid(test_client: FlaskClient, test_user: Dict[str, Any]) -> None:
    """Test median analysis with invalid field."""
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


def test_analyze_median_empty_data_returns_empty_list(test_client: FlaskClient, test_user: Dict[str, Any]) -> None:
    """Ensure analysis returns empty list when no data exists."""

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


# -------------------------- Saved Search Tests --------------------------

def test_save_search_correct(test_client: FlaskClient, test_user: Dict[str, Any]) -> None:
    """Test saving a search query successfully."""
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


def test_save_search_missing_name_and_query(test_client: FlaskClient, test_user: Dict[str, Any]) -> None:
    """Validate error handling for missing name or query in save search."""
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


def test_rerun_saved_search_success(test_client: FlaskClient, test_user: Dict[str, Any]) -> None:
    """Test successful rerun of a saved search."""
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


def test_rerun_saved_search_invalid_json(test_client: FlaskClient, test_user: Dict[str, Any]) -> None:
    """Check behavior when invalid JSON is passed in rerun."""
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


def test_delete_search_success(test_client: FlaskClient, test_user: Dict[str, Any]) -> None:
    """Test deleting a saved search for the logged-in user."""
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


def test_delete_search_failure(test_client: FlaskClient, test_user: Dict[str, Any]) -> None:
    """Ensure search delete fails if user does not own the search."""
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


# -------------------------- Autocomplete Tests --------------------------

def test_autocomplete_district_no_city(test_client: FlaskClient, test_user: Dict[str, Any]) -> None:
    """Ensure district autocomplete returns empty if no city is specified."""
    test_client.post("/login", data={
        "username": test_user["username"],
        "password": "Password@123"
    })
    response = test_client.get("/autocomplete/district?q=Cent")
    assert response.status_code == 200
    assert response.get_json() == []


def test_autocomplete_district_with_city(test_client: FlaskClient, test_user: Dict[str, Any]) -> None:
    """Test district autocomplete with valid city input."""
    test_client.post("/login", data={
        "username": test_user["username"],
        "password": "Password@123"
    })

    response = test_client.get("/autocomplete/district?city=Vilnius&q=Cent")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)


def test_autocomplete_city(test_client: FlaskClient, test_user: Dict[str, Any]) -> None:
    """Test city autocomplete endpoint returns list of cities."""
    test_client.post("/login", data={
        "username": test_user["username"],
        "password": "Password@123"
    })

    response = test_client.get("/autocomplete/city")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_search_no_filters(test_client: FlaskClient) -> None:
    """Test search route with no filters returns a response."""
    response = test_client.post("/search", data={})
    assert response.status_code == 200
    assert b"results" in response.data or b"No results found" in response.data


# -------------------------- Saved Searches & Analysis Page Access Control --------------------------

def test_search_city_filter(test_client: FlaskClient) -> None:
    """Search results should reflect provided city filter."""
    response = test_client.post("/search", data={"city": "Vilnius"})
    assert response.status_code == 200
    assert b"Vilnius" in response.data


def test_search_full_filters(test_client: FlaskClient) -> None:
    """Test search with all filters applied."""
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


def test_my_searches_requires_login(test_client: FlaskClient) -> None:
    """Ensure /my_searches page redirects to login when not authenticated."""
    # Make sure no user is logged in
    test_client.get("/logout", follow_redirects=True)
    response = test_client.get("/my_searches", follow_redirects=True)
    assert b"Login" in response.data


def test_my_searches_logged_in(test_client: FlaskClient, test_user: Dict[str, Any]) -> None:
    """Ensure logged-in user can access /my_searches page."""
    test_client.post("/login", data={
        "username": test_user["username"],
        "password": "Password@123"
    })
    response = test_client.get("/my_searches")
    assert response.status_code == 200
    assert b"My Saved Searches" in response.data


def test_analysis_page_requires_login(test_client: FlaskClient) -> None:
    """Ensure analysis page is restricted for unauthenticated users."""
    # Make sure no user is logged in
    test_client.get("/logout", follow_redirects=True)
    response = test_client.get("/analysis_page", follow_redirects=True)
    assert b"Login" in response.data


def test_analysis_page_logged_in(test_client: FlaskClient, test_user: Dict[str, Any]) -> None:
    """Ensure analysis page is accessible to logged-in users."""
    test_client.post("/login", data={
        "username": test_user["username"],
        "password": "Password@123"
    })
    response = test_client.get("/analysis_page")
    assert response.status_code == 200
    assert b"Interactive Chart" in response.data


def test_analyze_median_city_filter_applied(test_client: FlaskClient, test_user: Dict[str, Any]) -> None:
    """Ensure median analysis respects city filter."""
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