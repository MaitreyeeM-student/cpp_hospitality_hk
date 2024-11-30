# main/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from flask import Blueprint
from .models import db  # Import db from models.py

main_bp = Blueprint('main', __name__)


from . import routes  # Import routes after blueprint creation

from . import models  # Ensure models.py initializes before routes
from . import SNS_SQS
from . import s3_lamdba
from . import routes  # Ensure routes is last