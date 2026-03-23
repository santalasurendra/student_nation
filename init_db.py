from app import app, db, bcrypt
from models.user_model import User
import os

def init_db():
    with app.app_context():
        print("Initializing database...")
        db.create_all()
        
        # Ensure upload folders exist
        UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static/uploads')
        folders = [
            os.path.join(UPLOAD_FOLDER, 'donations'),
            os.path.join(UPLOAD_FOLDER, 'emergency_requests'),
            os.path.join(UPLOAD_FOLDER, 'team_images')
        ]
        for folder in folders:
            if not os.path.exists(folder):
                os.makedirs(folder)
                print(f"Created folder: {folder}")

        founder_email = 'surendrasaantala@gmail.com'
        founder = User.query.filter_by(email=founder_email).first()
        if not founder:
            hashed_pw = bcrypt.generate_password_hash('founder123').decode('utf-8')
            founder = User(name='SANTALA SURENDRA', email=founder_email, password=hashed_pw, role='Founder', email_verified=True)
            db.session.add(founder)
            db.session.commit()
            print("Founder account created.")
        else:
            print("Founder already exists.")
        print("Database initialization complete.")

if __name__ == "__main__":
    init_db()
