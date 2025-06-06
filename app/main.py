from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, login_user, logout_user, current_user
from .forms import RegisterForm, LoginForm, PropertySearchForm
from .db_init import app, mongo, bcrypt, User
import pandas as pd

from flask_wtf.csrf import generate_csrf
import json
from datetime import datetime
from bson import ObjectId
from typing import Any, Dict, List


@app.context_processor
def inject_csrf_token() -> Dict[str, str]:
    """
    Inject CSRF token into all Jinja2 templates.

    Returns:
        dict: CSRF token dictionary for template rendering.
    """
    return dict(csrf_token=generate_csrf())


@app.route("/")
def index() -> str:
    """
    Render the home page.

    Returns:
        str: Rendered index template.
    """
    return render_template("index.html")


@app.route("/logout")
@login_required
def logout() -> Any:
    """
    Log out the current user and redirect to index.

    Returns:
        Response: Redirect to homepage.
    """
    logout_user()
    return redirect(url_for("index"))


@app.route('/register', methods=["GET", 'POST'])
def register_user() -> str:
    """
    Register a new user.

    Returns:
        str: Rendered registration page or redirect on success/failure.
    """
    form = RegisterForm()
    users_collection = mongo.db.users

    if request.method == "POST":
        if not form.validate_on_submit():
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"{error}", "danger")

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        if users_collection.find_one({"username": username}):
            flash("Username already exists", "danger")
            return redirect(url_for('register_user'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        users_collection.insert_one({"username": username, "password": hashed_password})

        flash("Registration successful!", "success")
        return redirect(url_for('login'))

    return render_template("register_user.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login() -> str:
    """
    Authenticate and log in a user.

    Returns:
        str: Rendered login page or redirect on success.
    """
    form = LoginForm()
    users_collection = mongo.db.users

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = users_collection.find_one({"username": username})

        if user and bcrypt.check_password_hash(user["password"], password):
            login_user(User(user))
            return redirect(url_for("search_properties"))
        else:
            flash("Invalid username or password", "danger")

    return render_template("login.html", form=form)


@app.route("/search", methods=["GET", "POST"])
@login_required
def search_properties() -> str:
    """
    Search properties using multiple filters.

    Returns:
        str: Rendered search page with results.
    """
    form = PropertySearchForm()
    results: List[Dict[str, Any]] = []
    query: Dict[str, Any] = {}

    if request.method == "POST":
        if form.city.data:
            query["city"] = form.city.data
        if form.district.data:
            query["district"] = form.district.data

        if form.price_min.data or form.price_max.data:
            query["price"] = {}
            if form.price_min.data:
                query["price"]["$gte"] = form.price_min.data
            if form.price_max.data:
                query["price"]["$lte"] = form.price_max.data

        if form.size_min.data or form.size_max.data:
            query["size_m2"] = {}
            if form.size_min.data:
                query["size_m2"]["$gte"] = form.size_min.data
            if form.size_max.data:
                query["size_m2"]["$lte"] = form.size_max.data

        if form.price_m2_min.data or form.price_m2_max.data:
            query["price_per_m2"] = {}
            if form.price_m2_min.data:
                query["price_per_m2"]["$gte"] = form.price_m2_min.data
            if form.price_m2_max.data:
                query["price_per_m2"]["$lte"] = form.price_m2_max.data

        if form.number_of_rooms.data:
            query["number_of_rooms"] = form.number_of_rooms.data

        if query:
            results = list(mongo.db.properties.find(query))

    return render_template("search.html", form=form, results=results, query=query)


@app.route("/analyze_median", methods=["POST"])
@login_required
def analyze_selected_median() -> Any:
    """
    Return median value per city for a selected numeric field.

    Returns:
        JSON: Median values grouped by city.
    """
    data = request.get_json()
    field = data.get("field")
    city_filter = data.get("city")
    limit = int(data.get("limit", 0))

    if field not in {"price", "size_m2", "price_per_m2", "number_of_rooms"}:
        return jsonify({"error": "Invalid field"}), 400

    query: Dict[str, Any] = {}
    if city_filter:
        query["city"] = city_filter

    cursor = mongo.db.properties.find(query, {"_id": 0, field: 1, "city": 1})
    df = pd.DataFrame(list(cursor))

    if df.empty or field not in df.columns:
        return jsonify([])

    df = df.dropna(subset=[field])

    medians = (
        df.groupby("city")[field]
        .median()
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={field: "value"})
    )

    if limit > 0 and len(medians) > limit * 2 and not city_filter:
        top = medians.head(limit)
        bottom = medians.tail(limit)
        medians = pd.concat([top, bottom])

    return jsonify(medians.to_dict(orient="records"))


@app.route("/save_search", methods=["POST"])
@login_required
def save_search() -> Any:
    """
    Save a user's search query for later use.

    Returns:
        JSON: Success or error message.
    """
    data = request.get_json()
    name = data.get("name")
    query = data.get("query")

    if not name:
        return jsonify({"error": "Search name is required"}), 400

    if query is None:
        return jsonify({"error": "Query is missing"}), 400

    saved_search = {
        "user_id": current_user.id,
        "name": name,
        "query": query,
        "timestamp": datetime.utcnow()
    }

    mongo.db.saved_searches.insert_one(saved_search)

    return jsonify({"message": "Search saved!"}), 200


@app.route("/my_searches")
@login_required
def my_searches() -> str:
    """
    Display all saved searches for the logged-in user.

    Returns:
        str: Rendered template with saved searches.
    """
    searches = mongo.db.saved_searches.find({"user_id": current_user.id})
    return render_template("my_searches.html", searches=searches)


@app.route("/rerun_search", methods=["POST"])
@login_required
def rerun_saved_search() -> str:
    """
    Rerun a previously saved search query.

    Returns:
        str: Rendered search page with old query results.
    """
    try:
        query = json.loads(request.form.get("query"))
    except Exception:
        flash("Failed to parse saved query.", "danger")
        return redirect(url_for("my_searches"))

    results = list(mongo.db.properties.find(query))
    form = PropertySearchForm()
    return render_template("search.html", form=form, results=results, query=query)


@app.route("/delete_search/<search_id>", methods=["POST"])
@login_required
def delete_search(search_id: str) -> Any:
    """
    Delete a user's saved search by its ID.

    Args:
        search_id (str): The ID of the saved search to delete.

    Returns:
        Response: Redirect back to saved searches with feedback.
    """
    result = mongo.db.saved_searches.delete_one({
        "_id": ObjectId(search_id),
        "user_id": str(current_user.id)
    })

    if result.deleted_count:
        flash("Search deleted successfully.", "success")
    else:
        flash("Failed to delete search.", "danger")

    return redirect(url_for("my_searches"))


@app.route("/autocomplete/city")
@login_required
def autocomplete_city() -> Any:
    """
    Provide city names for autocomplete field.

    Returns:
        JSON: List of city suggestions.
    """
    cities = mongo.db.properties.distinct("city")
    return jsonify([{"id": city, "text": city} for city in sorted(cities)])


@app.route("/autocomplete/district", methods=["GET"])
@login_required
def autocomplete_district() -> Any:
    """
    Provide district names for a selected city for autocomplete.

    Returns:
        JSON: List of district suggestions.
    """
    city = request.args.get("city", "")
    q = request.args.get("q", "")
    if not city:
        return jsonify([])

    districts = mongo.db.properties.distinct("district", {
        "city": city,
        "district": {"$regex": f"^{q}", "$options": "i"}
    })

    return jsonify([{"id": d, "text": d} for d in sorted(districts)])


@app.route("/analysis_page")
@login_required
def analysis_page() -> str:
    """
    Render the analysis dashboard page.

    Returns:
        str: Rendered analysis template.
    """
    return render_template("analysis.html")


if __name__ == '__main__':
    app.run(debug=True)

# If time permits, implement email field
# CSS fill to fit img

# USE THIS TO RUN python -m app.main from real_estate_project dir
