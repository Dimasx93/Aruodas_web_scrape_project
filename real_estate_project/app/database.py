# database.py
from flask import Flask
from flask_login import UserMixin

from .extensions import login_manager, mongo, bcrypt, csrf
from bson.objectid import ObjectId

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/aruodas_apartments"
app.config['SECRET_KEY'] = "secret_key"

# Initialize extensions with the app
mongo.init_app(app)
bcrypt.init_app(app)
csrf.init_app(app)
login_manager.init_app(app)
login_manager.login_view = "login"

#Define the User class here
class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data["_id"])
        self.username = user_data["username"]
        self.password = user_data["password"]

@login_manager.user_loader
def load_user(user_id):
    user_data = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if user_data:
        return User(user_data)
    return None

#Access MongoDB collection
collection = mongo.db.properties
