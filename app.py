from flask import Flask, redirect, url_for
from flask_migrate import Migrate
import os
from main import db  
from main import main_bp
from auth import auth_bp  
from dotenv import load_dotenv
from main.SNS_SQS import setup_notification_services

load_dotenv()  
migrate = Migrate()  

def create_app():
    app = Flask(__name__)

    @app.route('/')
    def home():
        return redirect(url_for('auth.login'))

    
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f'postgresql://{os.getenv("DB_USERNAME")}:{os.getenv("DB_PASSWORD")}'
        f'@{os.getenv("DB_HOST")}/{os.getenv("DB_NAME")}')
    
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

    
    db.init_app(app)
    migrate.init_app(app, db) 
    
    
    with app.app_context():
        try:
            setup_notification_services()  
        except Exception as e:
            print(f"Error setting up notification services: {e}")

    # blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp, url_prefix='/main')

    return app


app = create_app()


if __name__ == '__main__':
    with app.app_context():
        
        #'''db.drop_all()''' # to reset or initialize the database tables
        db.create_all()  
    app.run(debug=True, port=8080)
