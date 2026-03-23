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

# Note: Database initialization is now handled in init_db.py.
# This prevents timeouts and race conditions on Render.
with app.app_context():
    db.create_all()


if __name__ == '__main__':
    # host='0.0.0.0' allows other devices on the same WiFi to access the server
    app.run(host='0.0.0.0', port=5000)
