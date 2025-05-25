from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, login_user, logout_user, current_user
from forms import RegisterForm, LoginForm, PropertySearchForm
from database import app, mongo, bcrypt, collection, User
import pandas as pd
import matplotlib

matplotlib.use('Agg')  # Use non-GUI backend suitable for scripts/web apps
import matplotlib.pyplot as plt
import io
import base64
from flask_wtf.csrf import generate_csrf
import json
from datetime import datetime
from bson import ObjectId


@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf())


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route('/register', methods=["GET", 'POST'])
def register_user():
    form = RegisterForm()
    users_collection = mongo.db.users

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        if users_collection.find_one({"username": username}):
            flash("Username already exists", "danger")
            return redirect(url_for('register_user'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        users_collection.insert_one({
            "username": username,
            "password": hashed_password
        })

        flash("Registration successful!", "success")
        return redirect(url_for('login'))

    return render_template("register_user.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    users_collection = mongo.db.users

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # Find user by username in MongoDB
        user = users_collection.find_one({"username": username})

        # Check password
        if user and bcrypt.check_password_hash(user["password"], password):
            login_user(User(user))
            return redirect(url_for("search_properties"))
        else:
            flash("Invalid username or password", "danger")

    return render_template("login.html", form=form)


@app.route("/search", methods=["GET", "POST"])
@login_required
def search_properties():
    form = PropertySearchForm()
    results = []
    query = {}

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

        # Only run the search if any filters were applied
        if query:
            results = list(mongo.db.properties.find(query))

    return render_template("search.html", form=form, results=results, query=query)


@app.route("/analyze_median", methods=["POST"])
@login_required
def analyze_selected_median():
    # Get selected field and optional query
    field = request.form.get("field")
    query_raw = request.form.get("query")  # Can be None or empty

    # Validate selected field
    if not field:
        return "Missing field selection."

    if field not in {"price", "size_m2", "price_per_m2", "number_of_rooms"}:
        return f"Invalid field: {field}"

    # Default to no filtering if no query passed
    if query_raw:
        try:
            query = json.loads(query_raw)
        except json.JSONDecodeError:
            return "Invalid query format."
    else:
        query = {}  # No filter applied

    # Fetch filtered or unfiltered data
    cursor = mongo.db.properties.find(query, {"_id": 0, field: 1, "city": 1})
    data = list(cursor)

    if not data:
        return "No matching data to analyze."

    # Convert to DataFrame
    df = pd.DataFrame(data)

    if df.empty or field not in df.columns:
        return f"No data found for field '{field}'."

    # Clean data
    df = df.dropna(subset=[field])

    # Group by city and compute median
    median_by_city = df.groupby("city")[field].median().sort_values(ascending=False)

    # Plot
    fig, ax = plt.subplots(figsize=(20, 6))  # Increase figure width
    median_by_city.plot(kind="bar", ax=ax)
    ax.set_title(f"Medium {field.replace("_", " ").title()} by City")
    ax.set_ylabel(field.replace("_", " ").title())
    ax.set_xlabel("City")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    # Convert to base64 image
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode("utf-8")
    buf.close()

    return render_template("analysis.html", image=image_base64, field=field)


@app.route("/save_search", methods=["POST"])
@login_required
def save_search():
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
def my_searches():
    searches = mongo.db.saved_searches.find({"user_id": current_user.id})
    return render_template("my_searches.html", searches=searches)


@app.route("/rerun_search", methods=["POST"])
@login_required
def rerun_saved_search():
    try:
        query = json.loads(request.form.get("query"))
    except Exception as e:
        flash("Failed to parse saved query.", "danger")
        return redirect(url_for("my_searches"))

    collection = mongo.db.properties
    results = list(collection.find(query))

    # Pass empty form since we're not repopulating fields from query here
    form = PropertySearchForm()

    return render_template("search.html", form=form, results=results, query=query)


@app.route("/delete_search/<search_id>", methods=["POST"])
@login_required
def delete_search(search_id):
    result = mongo.db.saved_searches.delete_one({
        "_id": ObjectId(search_id),
        "user_id": current_user.id  # ensure users can only delete their own
    })

    if result.deleted_count:
        flash("Search deleted successfully.", "success")
    else:
        flash("Failed to delete search.", "danger")

    return redirect(url_for("my_searches"))


@app.route("/autocomplete/city")
@login_required
def autocomplete_city():
    term = request.args.get("q", "")
    if not term:
        return jsonify([])

    # Query cities that start with the search term (case-insensitive)
    cities = mongo.db.properties.distinct("city", {"city": {"$regex": f"^{term}", "$options": "i"}})

    # Optional: limit to 10 results
    return jsonify(cities[:10])


@app.route("/autocomplete/district", methods=["GET"])
@login_required
def autocomplete_district():
    city = request.args.get("city", "")
    q = request.args.get("q", "")
    if not city:
        return jsonify([])

    # Find distinct districts within the given city and starting with query
    pipeline = [
        {"$match": {"city": {"$regex": f"^{city}$", "$options": "i"},
                    "district": {"$regex": f"^{q}", "$options": "i"}}},
        {"$group": {"_id": "$district"}},
        {"$limit": 10}
    ]
    districts = [d["_id"] for d in mongo.db.properties.aggregate(pipeline)]
    return jsonify(districts)


if __name__ == '__main__':
    app.run(debug=True)

# Show more info about the ads ie URL, pictures, saves the search, mark favourites, interactive graphics? d3.js JavaScript,
# search for specific city (like drop menu, or filter for non LT keyboard) for graphic or make it top last 5/10,
