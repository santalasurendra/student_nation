from flask import Flask
from config import Config
from utils.database import db
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_mail import Mail
import os

from models.user_model import User
from models.team_model import TeamMember
from models.request_model import EmergencyRequest
from models.donation_model import Donation, FundDistribution

from routes.main_routes import main_bp
from routes.admin_routes import admin_bp
from routes.auth_routes import auth_bp
from routes.founder_routes import founder_bp

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
bcrypt = Bcrypt(app)
mail = Mail(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth_bp.login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app.register_blueprint(main_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(founder_bp, url_prefix='/founder')

def create_initial_founder():
    with app.app_context():
        db.create_all()
        founder_email = 'surendrasaantala@gmail.com'
        founder = User.query.filter_by(email=founder_email).first()
        if not founder:
            hashed_pw = bcrypt.generate_password_hash('founder123').decode('utf-8')
            founder = User(name='SANTALA SURENDRA', email=founder_email, password=hashed_pw, role='Founder', email_verified=True)
            db.session.add(founder)
            db.session.commit()
            print("Founder account created. email: surendrasaantala@gmail.com password: founder123")

# Database initialization (required for first-time setup on Render)
with app.app_context():
    # Ensure upload folders exist
    for folder in [app.config['PAYMENT_SCREENSHOTS_FOLDER'], 
                  app.config['HOSPITAL_BILLS_FOLDER'], 
                  app.config['TEAM_IMAGES_FOLDER']]:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"Created folder: {folder}")
            
    db.create_all()
    create_initial_founder()

if __name__ == '__main__':
    # host='0.0.0.0' allows other devices on the same WiFi to access the server
    app.run(host='0.0.0.0', port=5000)
