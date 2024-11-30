# auth/__init__.py
from flask import Blueprint

# Create the Blueprint object
auth_bp = Blueprint('auth', __name__)

# Import routes after defining the Blueprint
from . import routes
