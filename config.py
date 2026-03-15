import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'santhiram_engineering_college_srec_secret_key'
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'student_nation.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload folders
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    TEAM_IMAGES_FOLDER = os.path.join(UPLOAD_FOLDER, 'team_images')
    HOSPITAL_BILLS_FOLDER = os.path.join(UPLOAD_FOLDER, 'hospital_bills')
    PAYMENT_SCREENSHOTS_FOLDER = os.path.join(UPLOAD_FOLDER, 'payment_screenshots')

    # Flask-Mail (Gmail SMTP)
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_USERNAME")

    # Base URL for email links
    # Change to your public domain when deployed
    BASE_URL = os.environ.get('BASE_URL') or "https://student-nation.onrender.com"

