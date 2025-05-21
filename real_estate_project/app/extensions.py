# extensions.py
from flask_login import LoginManager
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect

login_manager = LoginManager()
mongo = PyMongo()
bcrypt = Bcrypt()
csrf = CSRFProtect()
