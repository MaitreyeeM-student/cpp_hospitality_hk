from flask import Flask, redirect, url_for
from flask_migrate import Migrate
import os
from main import db  # Import db and blueprint
from main import main_bp
from auth import auth_bp  # Import auth blueprint
from dotenv import load_dotenv
from main.SNS_SQS import setup_notification_services

load_dotenv()  # Load environment variables from the .env file
migrate = Migrate()  # Initialize Migrate globally

# Flask application factory
def create_app():
    app = Flask(__name__)

    @app.route('/')
    def home():
        return redirect(url_for('auth.login'))

    # Use the loaded environment variables
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f'postgresql://{os.getenv("DB_USERNAME")}:{os.getenv("DB_PASSWORD")}'
        f'@{os.getenv("DB_HOST")}/{os.getenv("DB_NAME")}')
    
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

    # Initialize database and migrations
    db.init_app(app)
    migrate.init_app(app, db)  # Initialize Migrate with the app and db
    
    # Initialize notification services within app context
    with app.app_context():
        try:
            setup_notification_services()  # Initialize SNS, SQS, and subscriptions
        except Exception as e:
            print(f"Error setting up notification services: {e}")

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp, url_prefix='/main')

    return app


app = create_app()

# Entry point for running the Flask app locally
if __name__ == '__main__':
    with app.app_context():
        
        #'''db.drop_all()''' # Uncomment if you want to reset or initialize the database tables
        db.create_all()  # Create all tables if they don't exist
    app.run(debug=True, port=8080)
