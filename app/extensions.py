"""
Initialize Flask extensions for application-wide use.
These are initialized here and bound to the app in db_init.py (or database.py).
"""

from flask_login import LoginManager
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect

# Manages user sessions and authentication
login_manager: LoginManager = LoginManager()

# Handles connection to MongoDB
mongo: PyMongo = PyMongo()

# Provides password hashing and checking
bcrypt: Bcrypt = Bcrypt()

# Protects against Cross-Site Request Forgery
csrf: CSRFProtect = CSRFProtect()