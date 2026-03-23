import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "studentnationsecret")

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///site.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False

    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_USERNAME")

    # Base URL for email links
    BASE_URL = os.environ.get("BASE_URL", "https://student-nation-2o71.onrender.com")

    # Upload folders
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static/uploads')
    PAYMENT_SCREENSHOTS_FOLDER = os.path.join(UPLOAD_FOLDER, 'donations')
    HOSPITAL_BILLS_FOLDER = os.path.join(UPLOAD_FOLDER, 'emergency_requests')
    TEAM_IMAGES_FOLDER = os.path.join(UPLOAD_FOLDER, 'team_images')

