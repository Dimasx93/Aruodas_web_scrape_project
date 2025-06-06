from flask import Flask
from flask_login import UserMixin
from bson.objectid import ObjectId

from .extensions import login_manager, mongo, bcrypt, csrf

# Initialize Flask application
app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/aruodas_apartments"
app.config["SECRET_KEY"] = "secret_key"

# Initialize Flask extensions
mongo.init_app(app)
bcrypt.init_app(app)
csrf.init_app(app)
login_manager.init_app(app)
login_manager.login_view = "login"


class User(UserMixin):
    """
    Custom User class used by Flask-Login.

    Attributes:
        id (str): Stringified MongoDB user ID.
        username (str): Username of the user.
        password (str): Hashed password.
    """
    def __init__(self, user_data: dict) -> None:
        self.id: str = str(user_data["_id"])
        self.username: str = user_data["username"]
        self.password: str = user_data["password"]


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    """
    Load a user by ID for Flask-Login session management.

    Args:
        user_id (str): User ID from session.

    Returns:
        User or None: A User instance if found, else None.
    """
    user_data = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if user_data:
        return User(user_data)
    return None


# Access to MongoDB 'properties' collection
collection = mongo.db.properties